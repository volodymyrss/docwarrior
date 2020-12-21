import click
import odakb
import odakb.sparql
import subprocess
import yaml
import re

def read_metadata():
    try:
        oda_meta_data = yaml.load(open("oda.yaml").read(), Loader=yaml.SafeLoader)
    except IOError:
        oda_meta_data = {}
        click.echo("not found!")

    return oda_meta_data

@click.group()
def cli():
    pass

def discover_directory_remote():
    r = {}

    try:
        r['git'] = subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip()
    except Exception as e:
        print("no git remote url", e)

    try:
        r['redmine-wiki'] = yaml.load(open("redmine-wiki.yaml"))['url']
    except Exception as e:
        print("no redmine wiki url", e)

    return r

  
      

@cli.command()
@click.option("-t", "--tag", default=None, multiple=True)
def up(tag):
    oda_meta_data = read_metadata()
    adopt_tags(oda_meta_data, tag)

    remotes = discover_directory_remote()
    click.echo(f"remotes: {remotes}")

    for remote_kind, remote in remotes.items():
        name = None
        if 'github.com' in remote:
            name = remote.split("/")[-1][:-4]

        if 'overleaf' in remote:
            title = re.search(r'\\title\{(.*?)\}', open('main.tex').read()).groups()[0]
            print("found title:", title)
            name = title.lower().replace(" ", "_")

        if 'gitlab.astro.unige.ch' in remote:
            name = remote.split("/")[-1][:-4]
        
        if 'gitlab.com' in remote:
            name = remote.split("/")[-1][:-4]
        
        if 'redmine' in remote:
            name = remote.split("/")[-1].lower()

        odakb.sparql.insert(f"oda:{name} a oda:doc; oda:location \"{remote}\"")

    for tag in oda_meta_data.get('tags', []):
        c=f"oda:{name} oda:domain \"{tag}\""
        click.echo(c)
        odakb.sparql.insert(c)

def adopt_tags(oda_meta_data, tag):
    if tag is not None:
        for t in tag:
            for _t in t.split(","):
                click.echo(f"tagging {_t}")
                oda_meta_data['tags'] = list(set(oda_meta_data.get('tags', []) + [_t]))
        click.echo(f"current tags: {oda_meta_data['tags']}")

@cli.command()
@click.argument("tag")
def tag(tag):
    oda_meta_data = read_metadata()

    adopt_tags(oda_meta_data, [tag])

    yaml.dump(oda_meta_data, open("oda.yaml", "w"), sort_keys=True)

@cli.command()
@click.option("-f", "--output-format", default="md")
@click.option("-o", "--output-file", default=None)
def generate(output_format, output_file):
    d = odakb.sparql.select("?d a oda:doc; ?x ?y", "?d ?x ?y", tojdict=True)

    output = ""
        
    if output_format == "md":
        output += """
| URI            | Domains (Tags)    | Location (URL)   |
| :------------- | :---------------: | ---------------: |
"""
    else:
        raise Exception(f"unknown output format: {output_formast}")

    for k, v in d.items():
        if output_format == "md":
            r = f"| {k:50s} | {', '.join(v['oda:domain']):60s} | {'; '.join(v['oda:location']):80s} |"
            output += r + "\n"
        else:
            raise RuntimeError

    print(output)

    if output_file is not None:
        open(output_file, "wt").write(output)

if __name__ == "__main__":
    cli()
