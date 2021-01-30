import os
from collections import defaultdict
import openreview
import json
import curses
import time

YEAR = 2021
METADATA_FILE = f"iclr{YEAR}_metadata.json"


def download_iclr(client):
    # this function is a modified version of:
    # https://openreview-py.readthedocs.io/en/latest/getting_data.html

    print("getting metadata...")
    submissions = openreview.tools.iterget_notes(
        client, invitation=f"ICLR.cc/{YEAR}/Conference/-/Blind_Submission"
    )

    submissions_by_forum = {n.forum: n for n in submissions}
    meta_reviews = openreview.tools.iterget_notes(
        client, invitation=f"ICLR.cc/{YEAR}/Conference/Paper.*/-/Decision"
    )
    meta_reviews_by_forum = {n.forum: n for n in meta_reviews}
    metadata = []
    t1 = set(submissions_by_forum.keys())
    t2 = set(meta_reviews_by_forum.keys())
    for forum in t1.intersection(t2):
        forum_meta_review = meta_reviews_by_forum[forum]
        decision = forum_meta_review.content["decision"]
        submission_content = submissions_by_forum[forum].content
        forum_metadata = {
            "forum": forum,
            "decision": decision,
            "submission_content": submission_content,
        }
        metadata.append(forum_metadata)

    print("writing metadata to file...")
    # write the metadata, one JSON per line:
    with open(os.path.join(".", METADATA_FILE), "w") as file_handle:
        for forum_metadata in metadata:
            file_handle.write(json.dumps(forum_metadata) + "\n")


LEFT_ARROW = 260
RIGHT_ARROW = 261
Q = 113
P = 112
READING_LIST_FNAME = "reading_list.csv"
LAST_ID_VIEWED_FNAME = ".lastid"


def main(win):
    data = []
    with open(f"iclr{YEAR}_metadata.json", "r") as json_file:
        for i, line in enumerate(json_file):
            paper = json.loads(line)
            if "Accept" in paper["decision"]:
                data.append(paper)
    n_papers = len(data)
    win.nodelay(True)
    win.clear()

    reading_list = []
    # check if we've made some progress
    try:
        with open(READING_LIST_FNAME, "r") as f:
            for line in f:
                st_idx = int(line.split(",")[0]) + 1
    except:
        win.addstr("No progress detected. Starting from the beginning\n")
        st_idx = 0

    done = False

    # load last id viewed, not last id of added paper
    try:
        with open(LAST_ID_VIEWED_FNAME, 'r') as f:
            last_id = int(f.readline())
    except:
        # no .lastid
        last_id = 0

    # in case, a person went to the previous one multiple times, start from last added
    i = max(last_id, st_idx)


    while i < len(data):
        if done:
            break
        paper = data[i]
        win.addstr(f"-----> PROGRESS {i+1}/{n_papers} <-----\n")
        win.addstr(f"TITLE: {paper['submission_content']['title']}\n")
        win.refresh()
        win.addstr(f"AUTHORS: {paper['submission_content']['authors']}\n")
        try:
            win.addstr(
                f"TL;DR: {paper['submission_content']['one-sentence_summary']}\n"
            )
        except:
            win.addstr("TL;DR:\n")
        win.addstr(f"DECISION: {paper['decision']}\n")
        win.addstr(f"ABSTRACT: {paper['submission_content']['abstract']}\n\n")

        win.addstr(
            "[Right arrow key] to add. [Left arrow key] to skip. [p] to the previous one. [q] to quit (your progress will be saved).\n"
        )
        win.refresh()

        while True:
            key = win.getch()
            if key == RIGHT_ARROW:
                win.addstr("-------ADDED-------\n")
                win.refresh()
                time.sleep(0.2)
                reading_list.append(i)
                break
            elif key == LEFT_ARROW:
                win.addstr("-------SKIPPED-------\n")
                win.refresh()
                time.sleep(0.2)
                break
            elif key == Q:
                done = True
                break
            elif key == P:
                i-=2 # go to the previous one if skipped by mistake
                break
            else:
                time.sleep(0.01)
        win.clear()
        i+=1

    with open(READING_LIST_FNAME, "a") as f:
        for idx in reading_list:
            paper = data[idx]
            f.write(
                f"{idx}, {paper['submission_content']['title']}, https://openreview.net/forum?id={paper['forum']}\n"
            )
    with open(LAST_ID_VIEWED_FNAME, 'w') as f:
        # since we do +1 in a while loop
        # this will save us from failing when a person has gone through all of the papers
        f.write(f"{i-1}")

if __name__ == "__main__":
    if not os.path.exists(METADATA_FILE):
        guest_client = openreview.Client(baseurl="https://api.openreview.net")
        download_iclr(guest_client)
    curses.wrapper(main)
