import click
import summon as summon_module


# A bit weird click syntax here: necessary to
# see all available command with --help!
@click.group()
def cli():
    pass

@cli.command()
def summon():
    """Create a new machine"""
    summon_module.summon()


if __name__ == '__main__':
    cli()
