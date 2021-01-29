import os
from collections import defaultdict
import openreview
import json
import curses
import time

# TODO go back

CONFERENCE_URL = "https://openreview.net/group?id=ICLR.cc/2021/Conference"
METADATA_FILE = "iclr19_metadata.json"


def download_iclr19(client, outdir="./"):
    # this function was taken from here: https://openreview-py.readthedocs.io/en/latest/getting_data.html#retrieving-all-official-reviews-for-a-conference

    print("getting metadata...")
    # get all ICLR '19 submissions, reviews, and meta reviews, and organize them by forum ID
    # (a unique identifier for each paper; as in "discussion forum").
    submissions = openreview.tools.iterget_notes(
        client, invitation="ICLR.cc/2019/Conference/-/Blind_Submission"
    )
    submissions_by_forum = {n.forum: n for n in submissions}

    # There should be 3 reviews per forum.
    reviews = openreview.tools.iterget_notes(
        client, invitation="ICLR.cc/2019/Conference/-/Paper.*/Official_Review"
    )
    reviews_by_forum = defaultdict(list)
    for review in reviews:
        reviews_by_forum[review.forum].append(review)

    # Because of the way the Program Chairs chose to run ICLR '19, there are no "decision notes";
    # instead, decisions are taken directly from Meta Reviews.
    meta_reviews = openreview.tools.iterget_notes(
        client, invitation="ICLR.cc/2019/Conference/-/Paper.*/Meta_Review"
    )
    meta_reviews_by_forum = {n.forum: n for n in meta_reviews}

    # Build a list of metadata.
    # For every paper (forum), get the review ratings, the decision, and the paper's content.
    metadata = []
    for forum in submissions_by_forum:

        forum_reviews = reviews_by_forum[forum]
        review_ratings = [n.content["rating"] for n in forum_reviews]

        forum_meta_review = meta_reviews_by_forum[forum]
        decision = forum_meta_review.content["recommendation"]

        submission_content = submissions_by_forum[forum].content

        forum_metadata = {
            "forum": forum,
            "review_ratings": review_ratings,
            "decision": decision,
            "submission_content": submission_content,
        }
        metadata.append(forum_metadata)

    print("writing metadata to file...")
    # write the metadata, one JSON per line:
    with open(os.path.join(outdir, METADATA_FILE), "w") as file_handle:
        for forum_metadata in metadata:
            file_handle.write(json.dumps(forum_metadata) + "\n")


LEFT_ARROW = 260
RIGHT_ARROW = 261
Q = 113
READING_LIST_FNAME = "reading_list.csv"


def main(win):
    data = []
    with open("iclr19_metadata.json", "r") as json_file:
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
                reading_list.append(int(line.split(",")[0]))
        st_idx = reading_list[-1] + 1
    except:
        win.addstr("No progress detected. Starting from the beginning\n")
        st_idx = 0

    done = False
    for i in range(st_idx, len(data)):
        if done:
            break
        paper = data[i]

        win.addstr(f"-----> PROGRESS {i}/{n_papers} <-----\n")
        win.addstr(f"TITLE: {paper['submission_content']['title']}\n")
        win.addstr(f"AUTHORS: {paper['submission_content']['authors']}\n")
        try:
            win.addstr(f"TL;DR: {paper['submission_content']['TL;DR']}\n")
        except:
            win.addstr("TL;DR:\n")
        win.addstr(f"DECISION: {paper['decision']}\n")
        win.addstr(f"ABSTRACT: {paper['submission_content']['abstract']}\n")

        win.addstr(
            "[Right arrow key] to add. [Left arrow key] to skip. [q] to quit (your progress will be saved).\n"
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
            else:
                time.sleep(0.01)
        win.clear()

    with open(READING_LIST_FNAME, "w") as f:
        for idx in reading_list:
            paper = data[idx]
            f.write(
                f"{idx}, {paper['submission_content']['title']}, https://openreview.net/forum?id={paper['forum']}\n"
            )


if __name__ == "__main__":
    if not os.path.exists(METADATA_FILE):
        guest_client = openreview.Client(baseurl="https://api.openreview.net")
        download_iclr19(guest_client, ".")
    curses.wrapper(main)
