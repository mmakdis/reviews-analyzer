# Reviews visualizer

![Imgur](https://i.imgur.com/OoU7LaB.gif)

(the delay between slides was manual [which is either a space or an enter] just for the gif.)

Normally it's 1 minute, unless you change that.

You can set up a cron for the `main.py` script to generate these words that show up on the website. The website will read the `data/apps.json` file, again, every one hour (unless you change it.).

You can open up the console and type `reloadData()` to force reloading the data. This will make contact with Node.js.

However, the site needs to be refreshed to use the new data. This will be fixed in an upcoming update.