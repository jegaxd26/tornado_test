import tornado.ioloop
import click
import os

from coverage import Coverage
if os.getenv('COVERAGE'):
    coverInstance = Coverage()
    coverInstance.start()

import app


@click.group()
def cli():
    pass

@cli.command()
def start():
    app.run()

@cli.command()
def test(attr=None):
    from nose.core import TestProgram
    argv = [ 'nosetests',
             '--detailed-errors',
             '-s',
             '--stop',
             #'--verbosity=2',
             #'--with-profile',
    ]
    if attr:
        argv.append('-a'+attr)
    tp = TestProgram(argv=argv, exit=False)
    
@cli.command()
@click.pass_context
def coverage(ctx,attr=None):
    ctx.invoke(test,attr)
    coverInstance.stop()
    coverInstance.save()
    coverInstance.report()
    coverInstance.html_report(directory='coverage')
    coverInstance.erase()

if __name__ == '__main__':
    cli()
