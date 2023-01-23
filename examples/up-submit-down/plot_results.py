#!/usr/bin/env python3

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import pandas
import seaborn as sns


def read_json(filename):
    """
    Read a file into a text blob.
    """
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


def plot_outputs(raw, plotname, ext="pdf"):
    """
    Parse results.json into dataframe and plots to save.
    """
    # Let's save the following, with runid as index
    columns = ["minicluster_size", "job_type", "time_seconds", "time_type"]

    # Let's first organize distributions of times
    data = []
    index = []
    for jobname, item in raw["info"].items():
        index += [jobname, jobname, jobname]
        jobtype = jobname.split("-minicluster-size")[0].rsplit("-", 1)[0]

        # This is how flux-cloud organized the output
        minicluster_size = int(jobname.rsplit("size-", 1)[-1])

        # Manual melt :)
        data.append([minicluster_size, jobtype, item["runtime"], "runtime"])
        data.append(
            [
                minicluster_size,
                jobtype,
                item["start_to_output_seconds"],
                "output_seconds",
            ]
        )
        data.append(
            [minicluster_size, jobtype, item["start_to_info_seconds"], "info_seconds"]
        )

    # Assemble the data frame, index is the runids
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data
    df.to_csv("results-df.csv")

    # We need colors!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()

    palette = {}
    for size in df.time_type.unique():
        palette[size] = hexcolors.pop(0)

    # Sort by size
    palette = dict(sorted(palette.items()))

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        df,
        title="Flux MiniCluster Time Variation",
        tag="minicluster_times",
        ydimension="time_seconds",
        palette=palette,
        ext=ext,
        plotname=plotname,
    )


def make_plot(df, title, tag, ydimension, palette, ext="pdf", plotname="lammps"):
    """
    Helper function to make common plots.
    """
    ext = ext.strip(".")
    plt.figure(figsize=(12, 12))
    sns.set_style("dark")
    ax = sns.boxplot(
        x="job_type",
        y=ydimension,
        hue="time_type",
        data=df,
        whis=[5, 95],
        palette=palette,
    )
    plt.title(title)
    plt.legend([], [], frameon=False)
    ax.set_xlabel("Job Type", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles, list(palette))
    plt.savefig(f"{tag}_{plotname}.{ext}")
    plt.clf()


def get_parser():
    """
    Process results file into plots.
    """
    parser = argparse.ArgumentParser(description="Plot LAMMPS outputs")
    parser.add_argument("results_json", help="results json file", nargs="?")
    parser.add_argument(
        "-p",
        "--plotname",
        default="lammps",
        help="base name for plot output files",
    )
    parser.add_argument(
        "-e",
        "--extension",
        dest="extension",
        default="pdf",
        help="image extension to use (defaults to pdf)",
    )
    return parser


def main():
    """
    Read in results json, and make plots.
    """
    parser = get_parser()
    args = parser.parse_args()
    if not os.path.exists(args.results_json):
        sys.exit(f"{args.results_json} does not exist.")
    data = read_json(args.results_json)
    plot_outputs(data, args.plotname, ext=args.extension)


if __name__ == "__main__":
    main()
