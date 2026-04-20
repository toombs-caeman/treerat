from asyncio import Queue, QueueShutDown, TaskGroup, run
from abc import ABC, abstractmethod
from base2 import *

class LanguageDriver(ABC):
    parser:Parser
    evaluator:Evaluator
    prompt = '> '

    @abstractmethod
    @classmethod
    def from_sysargs(cls) -> 'LanguageDriver':
        """
        construct a language driver from cli arguments.

        the intended use is:
        if __name__ == "__main__":
            LanguageDriver.from_args().run()
        """

    @abstractmethod
    async def get_user_input(self) ->str:
        """get a line of user input."""
        raise NotImplementedError()

    @abstractmethod
    async def handleInterrupt(self) -> bool:
        return True

    async def input(self, stdin:Queue[str]):
        shouldShutdown = False
        while not shouldShutdown:
            try:
                await stdin.put(await self.get_user_input())
            except EOFError:
                shouldShutdown = True
            except KeyboardInterrupt:
                shouldShutdown = await self.handleInterrupt()
        stdin.shutdown()

    async def parse(self, stdin:Queue[str], stdast:Queue[ast], stderr:Queue[Exception]):
        try:
            while True:
                try:
                    src = await stdin.get()
                    for a in self.parser.parse(src).toAst(src):
                        await stdast.put(a)
                except ParseError as e:
                    await stderr.put(e)
                finally:
                    stdin.task_done()
        except QueueShutDown:
            stdast.shutdown()

    async def eval(self, stdast: Queue[ast], stdout: Queue[lexen], stderr: Queue[Exception]):
        #TODO
        self.evaluator

    async def run_async(self):
        stdin: Queue[str] = Queue()
        stdast: Queue[ast] = Queue()
        stdout: Queue[lexen] = Queue()
        stderr: Queue[Exception] = Queue()
        async with TaskGroup() as tg:
            input = tg.create_task(self.input(stdin))
            parse = tg.create_task(self.parse(stdin, stdast, stderr))
            eval = tg.create_task(self.eval(stdast, stdout, stderr))
            output = tg.create_task(self.output(stdout, stderr))

    def run(self):
        run(self.run_async())


