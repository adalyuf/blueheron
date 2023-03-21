from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import asyncio
import time

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(
            say_after(1, 'hello'))

        task2 = tg.create_task(
            say_after(2, 'world'))

        print(f"started at {time.strftime('%X')}")

    # The await is implicit when the context manager exits.

    print(f"finished at {time.strftime('%X')}")


class Command(BaseCommand):
    help = "import a list of domains at first launch"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str)

    def handle(self, *args, **options):
        asyncio.run(main())





