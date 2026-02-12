from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.chat.models import Message

class Command(BaseCommand):
    help = 'Checks which messages would be deleted based on a 5-minute cutoff (Debug Tool)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🔍 Starting Cleanup Logic Check...'))

        # 1. الوقت الحالي حسب توقيت السيرفر
        now = timezone.now()
        self.stdout.write(f"🕒 Server Time Now: {now}")

        # 2. وقت الحذف (قبل 5 دقائق للتجربة)
        # ملاحظة: هذا الرقم يجب أن يطابق ما وضعته في tasks.py للاختبار
        cutoff = now - timedelta(minutes=5)
        self.stdout.write(self.style.ERROR(f"✂️  Cutoff Time (5 mins ago): {cutoff}"))
        self.stdout.write("-" * 50)

        # 3. فحص الرسائل (نجلب أحدث 20 رسالة)
        messages = Message.objects.all().order_by('-timestamp')[:20]
        
        if not messages:
            self.stdout.write("No messages found in database.")
            return

        for msg in messages:
            # المقارنة: هل وقت الرسالة أقدم من وقت القص؟
            is_old = msg.timestamp < cutoff
            
            # حساب الفرق بالدائق
            diff = now - msg.timestamp
            minutes_ago = int(diff.total_seconds() / 60)

            msg_info = f"ID: {str(msg.id)[:8]}... | Time: {msg.timestamp.strftime('%H:%M:%S')} ({minutes_ago}m ago)"
            
            if is_old:
                self.stdout.write(self.style.SUCCESS(f"✅ {msg_info} -> WOULD BE DELETED"))
            else:
                self.stdout.write(self.style.NOTICE(f"❌ {msg_info} -> KEPT (Too new)"))

        self.stdout.write("-" * 50)
        self.stdout.write("ℹ️  Note: If messages are marked ✅ but not deleted, check if Celery Beat is running.")