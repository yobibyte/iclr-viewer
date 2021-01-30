# iclr-viewer
Go through the list of accepted papers for ICLR in terminal and add them to your reading list.


## Dependencies
```
pip install openreview-py
```

## Usage

`python main.py` to start (it will download metadata at first run).
Go through the list to select papers and add those you like.
If you quit, the progress will be saved, and you can continue from where you stopped.
`reading_list.csv` will contain papers you've added including their titles and links.

| Key        | Are           |
| ------------- |-------------|
| `right arrow`     | add paper to your list|
| `left arrow`      | skip and go to next|
| `p`| go to the previous paper|
| `q`| save progress and quit|
