# bing_dl_tags
Download Images from Bing with Tag/Description Files

Code originally from:
https://github.com/gurugaurav/bing_image_downloader

Go buy him a coffee or something.

Disclaimer
This program lets you download tons of images from Bing. Please do not download or use any image that violates its copyright terms.


Usage:

change the following values, then run:

    query: str = "Lambda Lambda Lambda"

    output_dir: str = "p:/bing/" #yes, put the slash at the end
    adult_filter: str = "off" # or "on"
    timeout: int = 60
    filter: str = "+filterui:photo-photo"

                # "+filterui:photo-linedrawing"
                # "+filterui:photo-photo"
                # "filterui:photo-clipart"
                # "+filterui:photo-animatedgif"
                # "+filterui:photo-transparent"
    limit: int = 1000
    cust_w = 640 # Custom Width Filter
    cust_h = 640 # Custom Width Filter
