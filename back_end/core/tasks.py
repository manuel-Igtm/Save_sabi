"""
Celery tasks for Save Sabi.

This module contains asynchronous tasks for:
- Budget rule evaluation
- Nudge delivery
- Cleanup operations
- Scheduled summaries
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def evaluate_wallet_rules(self, wallet_id: str):
    """
    Evaluate all budget rules for a specific wallet.
    
    Called after transactions or periodically.
    
    Args:
        wallet_id: UUID of the wallet to evaluate
    """
    from core.models import Wallet
    from core.services import nudges
    
    try:
        wallet = Wallet.objects.get(id=wallet_id)
        created_nudges = nudges.evaluate_rules(wallet)
        
        logger.info(f"Evaluated rules for wallet {wallet_id}, created {len(created_nudges)} nudges")
        
        # Queue nudge delivery for each created nudge
        for nudge in created_nudges:
            deliver_nudge.delay(str(nudge.id))
        
        return {'wallet_id': str(wallet_id), 'nudges_created': len(created_nudges)}
    
    except Wallet.DoesNotExist:
        logger.error(f"Wallet {wallet_id} not found")
        return {'error': 'Wallet not found'}
    
    except Exception as e:
        logger.error(f"Error evaluating rules for wallet {wallet_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def evaluate_all_daily_rules(self):
    """
    Evaluate daily budget rules for all active wallets.
    
    Called by Celery beat schedule every hour.
    """
    from core.models import Wallet, BudgetRule, RulePeriod
    from core.services import nudges
    
    try:
        # Get wallets with active daily rules
        wallet_ids = BudgetRule.objects.filter(
            is_active=True,
            period=RulePeriod.DAILY
        ).values_list('wallet_id', flat=True).distinct()
        
        total_nudges = 0
        
        for wallet_id in wallet_ids:
            try:
                wallet = Wallet.objects.get(id=wallet_id, is_active=True)
                created_nudges = nudges.evaluate_rules(wallet)
                total_nudges += len(created_nudges)
                
                for nudge in created_nudges:
                    deliver_nudge.delay(str(nudge.id))
            
            except Wallet.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"Error evaluating rules for wallet {wallet_id}: {e}")
                continue
        
        logger.info(f"Daily rule evaluation complete. Processed {len(wallet_ids)} wallets, created {total_nudges} nudges")
        
        return {'wallets_processed': len(wallet_ids), 'nudges_created': total_nudges}
    
    except Exception as e:
        logger.error(f"Error in daily rule evaluation: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def deliver_nudge(self, nudge_id: str):
    """
    Deliver a nudge via the appropriate channel.
    
    Currently supports in-app notifications.
    Future: email, push notifications, SMS.
    
    Args:
        nudge_id: UUID of the nudge to deliver
    """
    from core.models import Nudge, DeliveryMethod
    
    try:
        nudge = Nudge.objects.select_related('wallet__owner').get(id=nudge_id)
        
        if nudge.sent_via == DeliveryMethod.EMAIL:
            # TODO: Implement email delivery
            logger.info(f"Would send email for nudge {nudge_id}")
            pass
        
        elif nudge.sent_via == DeliveryMethod.PUSH:
            # TODO: Implement push notification delivery
            logger.info(f"Would send push notification for nudge {nudge_id}")
            pass
        
        elif nudge.sent_via == DeliveryMethod.SMS:
            # TODO: Implement SMS delivery
            logger.info(f"Would send SMS for nudge {nudge_id}")
            pass
        
        else:
            # In-app notification - already created, nothing to do
            logger.debug(f"In-app nudge {nudge_id} delivered")
        
        return {'nudge_id': str(nudge_id), 'delivered': True}
    
    except Nudge.DoesNotExist:
        logger.error(f"Nudge {nudge_id} not found")
        return {'error': 'Nudge not found'}
    
    except Exception as e:
        logger.error(f"Error delivering nudge {nudge_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def cleanup_old_nudges(days: int = 90):
    """
    Clean up old read nudges.
    
    Called daily by Celery beat.
    
    Args:
        days: Delete nudges older than this many days
    """
    from core.services import nudges
    
    deleted_count = nudges.cleanup_old_nudges(days)
    
    logger.info(f"Cleaned up {deleted_count} old nudges")
    
    return {'deleted_count': deleted_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_goal_progress(self, wallet_id: str):
    """
    Update progress for all goals in a wallet.
    
    Called after transactions affect savings.
    
    Args:
        wallet_id: UUID of the wallet
    """
    from core.models import Wallet, Goal, GoalStatus
    from core.services import goals as goal_service
    
    try:
        wallet = Wallet.objects.get(id=wallet_id)
        active_goals = Goal.objects.filter(wallet=wallet, status=GoalStatus.ACTIVE)
        
        for goal in active_goals:
            progress = goal_service.track_goal_progress(goal)
            
            # Check if goal just completed
            if progress['is_completed'] and goal.status != GoalStatus.COMPLETED:
                goal.status = GoalStatus.COMPLETED
                goal.save()
                
                # Create congratulations nudge
                from core.services.nudges import create_tip_nudge
                create_tip_nudge(
                    wallet,
                    f"Congratulations! You've reached your goal '{goal.name}'! 🎉",
                    title="Goal Completed!"
                )
        
        logger.info(f"Updated progress for {active_goals.count()} goals in wallet {wallet_id}")
        
        return {'wallet_id': str(wallet_id), 'goals_updated': active_goals.count()}
    
    except Wallet.DoesNotExist:
        logger.error(f"Wallet {wallet_id} not found")
        return {'error': 'Wallet not found'}
    
    except Exception as e:
        logger.error(f"Error updating goal progress for wallet {wallet_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def send_daily_summary(user_id: str):
    """
    Send daily summary to a user.
    
    Args:
        user_id: UUID of the user
    """
    from django.contrib.auth import get_user_model
    from core.models import Wallet
    from core.services import summaries
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        primary_wallet = Wallet.objects.get(owner=user, is_primary=True, is_active=True)
        
        summary = summaries.compute_30day_summary(primary_wallet)
        
        # TODO: Format and send via email
        logger.info(f"Daily summary for user {user_id}: {summary['savings_rate']}% savings rate")
        
        return {'user_id': str(user_id), 'summary_sent': True}
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': 'User not found'}
    
    except Wallet.DoesNotExist:
        logger.error(f"Primary wallet not found for user {user_id}")
        return {'error': 'Primary wallet not found'}
    
    except Exception as e:
        logger.error(f"Error sending daily summary for user {user_id}: {e}")
        return {'error': str(e)}


@shared_task
def check_streak_breaks():
    """
    Check for broken savings streaks and notify users.
    
    Called daily.
    """
    from core.models import Wallet, SavingsStreak
    from core.services.nudges import create_tip_nudge
    
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    
    # Find streaks that might be breaking
    breaking_streaks = SavingsStreak.objects.filter(
        last_savings_date=yesterday,
        current_streak__gte=3  # Only notify if they had a streak of 3+ days
    ).select_related('wallet__owner')
    
    notifications_sent = 0
    
    for streak in breaking_streaks:
        create_tip_nudge(
            streak.wallet,
            f"Your {streak.current_streak}-day savings streak is about to end! "
            f"Make a deposit today to keep it going! 💪",
            title="Keep Your Streak!"
        )
        notifications_sent += 1
    
    logger.info(f"Sent {notifications_sent} streak break warnings")
    
    return {'notifications_sent': notifications_sent}


@shared_task
def calculate_monthly_stats():
    """
    Calculate and store monthly statistics for all wallets.
    
    Called at the beginning of each month.
    """
    from core.models import Wallet
    from core.services import summaries
    
    wallets = Wallet.objects.filter(is_active=True)
    stats_calculated = 0
    
    for wallet in wallets:
        try:
            summary = summaries.compute_summary(wallet, range_type='30d')
            
            # Store in metadata or separate stats table if needed
            # For now, just log
            logger.info(
                f"Monthly stats for wallet {wallet.id}: "
                f"savings_rate={summary['savings_rate']}%, "
                f"total_saved={summary['total_saved']}"
            )
            stats_calculated += 1
        
        except Exception as e:
            logger.error(f"Error calculating stats for wallet {wallet.id}: {e}")
            continue
    
    return {'wallets_processed': stats_calculated}
