'use strict';

const express = require('express');
const app = express();
const fs = require('fs');
const bodyParser = require('body-parser');
var _ = require('lodash');
var CronJob = require('cron').CronJob;

app.set('view engine', 'ejs')
app.use(express.static('public'));
app.use(bodyParser.urlencoded({ extended: true }));

var appsData = getJSON('data/apps.json');

// console.log(allData);

/**
 * @param {String} filePath     The path for the JSON file.
 */

function readAppsData() {
  appsData = getJSON('data/apps.json');
}

function getJSON(filePath) {
  let rawdata = fs.readFileSync(filePath);
  let config = JSON.parse(rawdata);
  return config;
}

function sortJSON() {
  var allData = {};  
  readAppsData();
  appsData.forEach(element => {
    allData[element._id.$oid] = element;
    allData[element._id.$oid].comments = [];
    delete allData[element._id.$oid]._id;
  });
  
  let reviewsData = getJSON('data/review.json');
  reviewsData.forEach(element => {
    if (allData[element.app.$oid] !== undefined) {
      allData[element.app.$oid].comments.push(element);
      delete allData[element.app.$oid].comments.app;
    }

    allData[element.app.$oid].comments.sort(function(a, b) {
      return a["timestamp"]["$date"] - b["timestamp"]["$date"];
    });
  });

  return allData;
}

app.get('/', function (req, res) {
  var allData = sortJSON();
  res.render('index', {"data": allData});
});


app.post("/reload", function(req, res) {
  readAppsData();
  res.status(200).send({"appsData": appsData});
});

app.listen(3000, function () {
  console.log('Listening on port 3000.');
});