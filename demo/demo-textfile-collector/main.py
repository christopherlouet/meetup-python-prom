import os
import resource
import shutil
import typer
import xml.etree.ElementTree as ElementTree

from lxml import etree
from rich import print
from typing import List, Optional
from typing_extensions import Annotated


def build_store_details(root: ElementTree) -> dict:
    """
    Count the number of operations per item.
    :param root: Root node.
    :return: Store detail.
    """
    store_details = {}
    for a in root:
        if "operation" in a.attrib:
            tag = a.tag.lower()
            if tag not in store_details:
                store_details[tag] = {
                    "count": 1,
                    "create": 0,
                    "update": 0,
                    "delete": 0
                }
            else:
                store_details[tag]["count"] += 1
            operation = a.attrib['operation']
            store_details[tag][operation] += 1
    return store_details


def create_metrics(store_details: dict, filter_names: List[str], store_count_total: int, dry_run: bool):
    """
    Creation of metrics relating to the store, in text collector format.
    :param store_details: Store information details.
    :param filter_names: Filter by name.
    :param store_count_total: Total number of lines.
    :param dry_run: Dry run mode.
    """
    metric_path = "/var/node_exporter/store.prom"
    metric_path_new = "/tmp/store.new.prom"
    metrics = []
    info_path = '{path="/tmp/store.xml"}'

    # Filter metrics
    store_items = {}
    if len(filter_names) > 0:
        for key, value in store_details.items():
            for filter_name in filter_names:
                if key == filter_name:
                    store_items[key] = value
    else:
        store_items = store_details
    store_items = dict(sorted(store_items.items()))

    print("Adding metric [green]Total number of lines[/green]")

    metrics.append("# HELP store_total_rows Total rows in store")
    metrics.append("# TYPE store_total_rows gauge")
    metrics.append(f"store_total_rows {info_path} {store_count_total}")

    for item in store_items:
        print(f"Adding metrics [green]{item}[/green]")

        store_type_count = store_items[item]["count"]
        store_type_create = store_items[item]["create"]
        store_type_update = store_items[item]["update"]
        store_type_delete = store_items[item]["delete"]

        metrics.append(f"# HELP store_{item}_total_rows {item} rows in store")
        metrics.append(f"# TYPE store_{item}_total_rows gauge")
        metrics.append(f"store_{item}_total_rows {info_path} {store_type_count}")

        metrics.append(f"# HELP store_{item}_create_rows {item} create rows in store")
        metrics.append(f"# TYPE store_{item}_create_rows gauge")
        metrics.append(f"store_{item}_create_rows {info_path} {store_type_create}")

        metrics.append(f"# HELP store_{item}_update_rows {item} update rows in store")
        metrics.append(f"# TYPE store_{item}_update_rows gauge")
        metrics.append(f"store_{item}_update_rows {info_path} {store_type_update}")

        metrics.append(f"# HELP store_{item}_delete_rows {item} delete rows in store")
        metrics.append(f"# TYPE store_{item}_delete_rows gauge")
        metrics.append(f"store_{item}_delete_rows {info_path} {store_type_delete}")

    if not dry_run:
        if os.path.exists(metric_path_new):
            os.remove(metric_path_new)
        # Writing metrics
        metric_file = open(metric_path_new, "w")
        for metric in metrics:
            metric_file.writelines(f"{metric}\n")
        metric_file.close()
        # Copy
        shutil.copyfile(metric_path_new, metric_path)
    else:
        print(f"[magenta]File content {metric_path} :[/magenta]")
        for metric in metrics:
            print(metric)


def store_count(root: ElementTree):
    """
    Number of lines in the file.
    :param root: Root node.
    :return: Number of lines.
    """
    count = sum(1 for _ in root.iter("*")) - 1
    return count


def init_memory_allocation(memory_allocation: float):
    """
    Memory allocation.
    :param memory_allocation: Taille en Go.
    """
    if os.path.isfile('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        with open('/sys/fs/cgroup/memory/memory.limit_in_bytes') as limit:
            mem = int(limit.read())
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    x = bytearray(round(memory_allocation)*1024*1024*1024)


def main(demo_file: str = "sample.xml",
         fruit: Annotated[Optional[List[str]], typer.Option()] = (),
         memory_allocation: float = 0.5,
         dry_run: bool = False):
    """
    Script utility to generate metrics from demo.xml file.
    :param demo_file: Path to demo.xml file.
    :param fruit: Filtrer les données du store par fruit.
    :param memory_allocation: Memory to be allocated in GB for processing.
    :param dry_run: Display data only.
    """
    print(f"demo_file: {demo_file}")
    init_memory_allocation(memory_allocation)

    print(f"File processing: {demo_file}")
    with open(demo_file) as f:
        parser_xml = etree.XMLParser(encoding="utf-8", recover=True)
        store = ElementTree.fromstring(f.read(), parser_xml)

    store_details = build_store_details(store)
    store_count_total = store_count(store)
    create_metrics(store_details, fruit, store_count_total, dry_run)


if __name__ == "__main__":
    typer.run(main)
