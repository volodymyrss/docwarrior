import click
import odakb
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
    git_remote = subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip()

    return git_remote

@cli.command()
def up():
    oda_meta_data = read_metadata()

    remote = discover_directory_remote()
    click.echo(f"remote: {remote}")

    name = None
    if 'github.com' in remote:
        name = remote.split("/")[-1][:-4]

    if 'overleaf' in remote:
        title = re.search(r'\\title\{(.*?)\}', open('main.tex').read()).groups()[0]
        print("found title:", title)
        name = title.lower().replace(" ", "_")



    odakb.sparql.insert(f"oda:{name} a oda:doc; oda:location \"{remote}\"")

    for tag in oda_meta_data.get('tags', []):
        c=f"oda:{name} oda:domain \"{tag}\""
        click.echo(c)
        odakb.sparql.insert(c)


@cli.command()
@click.option("-t", "--tag", default=None)
def tag(tag):
    oda_meta_data = read_metadata()

    if tag is not None:
        click.echo(f"tagging {tag}")
        oda_meta_data['tags'] = list(set(oda_meta_data.get('tags', []) + [tag]))

    yaml.dump(oda_meta_data, open("oda.yaml", "w"))

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
