'use strict';

const express = require('express');
const app = express();
const fs = require('fs');
const bodyParser = require('body-parser');
var _ = require('lodash');

app.set('view engine', 'ejs')
app.use(express.static('public'));
app.use(bodyParser.urlencoded({ extended: true }));

var appsData = getJSON('data/apps.json');
var allData = {};

appsData.forEach(element => {
  allData[element["_id"]["$oid"]] = element;
  allData[element["_id"]["$oid"]]["comments"] = [];
  delete allData[element["_id"]["$oid"]]["_id"];
});

// console.log(allData);

/**
 * @param {String} filePath     The path for the JSON file.
 */
function getJSON(filePath) {
  let rawdata = fs.readFileSync(filePath);
  let config = JSON.parse(rawdata);
  return config;
}

app.get('/', function (req, res) {
  let reviewsData = getJSON('data/review.json');
  reviewsData.forEach(element => {
    if (allData[element["app"]["$oid"]] !== undefined) {
      allData[element["app"]["$oid"]]["comments"].push(element);
      delete allData[element["app"]["$oid"]]["comments"]["app"]
    }

    allData[element["app"]["$oid"]]["comments"].sort(function(a, b) {
      return a["timestamp"]["$date"] - b["timestamp"]["$date"];
    });
  });

  res.render('index', {"data": allData});
})

app.post('/', function(req, res) {
  // res.render('index', allData);
})

app.get("/parse", function(req, res) {
    res.send("Test");
    console.log(appsData.length);
})

app.listen(3000, function () {
  console.log('Listening on port 3000.');
})