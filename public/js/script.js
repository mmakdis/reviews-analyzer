/*jshint esversion: 8 */

var avgRatings = {};
var avgKeys = [];
var alignHoriz = {0: "left", 1: "center", 2: "right"};
var data = {};
var dataKeys = [];
var _dataKeys = [];

/**
 * Get a random image from Unsplash and use it as the background.
 */
function renderItem(){
  fetch("https://source.unsplash.com/1920x1080/?nature,water,space").then((response)=> {   
    var body = document.getElementsByTagName('body')[0];
    body.style.backgroundImage = `url(${response.url})`;
  });
}

function animationEnds() {
}

const delay = ms => new Promise(res => setTimeout(res, ms));


function animateCSS(element, animationName, callback) {
  element.classList.add('animated', animationName);

  function handleAnimationEnd() {
      element.classList.remove('animated', animationName);
      element.removeEventListener('animationend', handleAnimationEnd);

      if (typeof callback === 'function') callback();
  }

  element.addEventListener('animationend', handleAnimationEnd);
}

function animateButtons(move) {
  var buttons = document.getElementsByClassName("button");
  for(var i = 0; i < buttons.length; i++) {
    if (move) {
      buttons.item(i).setAttribute("id", "movetxt");
    }
    else {
      animateCSS(buttons.item(i), 'bounceIn');
    }
  }
}

async function makeContent(contentIndex) {
  var element = document.createElement("div");
  element.setAttribute("class", "content");
  document.getElementById("slideshow").appendChild(element);
  // document.body.appendChild(element);
  // addButtons(element);
  addButtons(contentIndex);
}

async function addButtons(contentIndex) {
  for(var i=0; i<3; i++) {
    var element = document.createElement("button");
    element.setAttribute("href", "#");
    element.setAttribute("class", `button ${alignHoriz[i]}`);
    element.setAttribute("name", _dataKeys[i]);
    element.innerText = data[_dataKeys[i]].app;
    document.getElementsByClassName("content")[contentIndex].appendChild(element);
    // contentIndex.appendChild(element);
  }
  _dataKeys.splice(0, 3);

  animateButtons(false);
  await delay(1050);
  addContainers(contentIndex);
}

function addContainers(contentIndex) {
  for(var i=0; i<3; i++) {
    var element = document.createElement("div");
    element.setAttribute("id", `${dataKeys[i]}`);
    element.setAttribute("class", `container animated zoomIn ${alignHoriz[i]}`);
    var logo = data[dataKeys[i]].source === "Apple Store" ? "iOS" :
          data[dataKeys[i]].source === "Google Play" ? "Android" : "";

    var _coef = data[dataKeys[i]].voc_coef;
    var sentence = "";
    var positives = "";
    var negatives = "";
    var html = "";
    if (typeof _coef === "string"
        || (_coef.positives.length == 0
        || _coef.negatives.length == 0)) {
      sentence = "Niet genoeg reviews.";
    }
    else {
      for (var positive in _coef.positives) {positives += `${_coef.positives[positive]}, `;}
      for (var negative in _coef.negatives) {negatives += `${_coef.negatives[negative]}, `;}

      positives = positives.substring(0, positives.length - 2);
      negatives = negatives.substring(0, negatives.length - 2);
    }
    
    if (sentence !== "") {
      html = `
      <i class="fa fa-question-circle qm" aria-hidden="true" style="margin: auto;"></i>
      <div class="ner animated flash slower delay-5s" style="margin: auto;">${sentence}</div>`;
    }
    else {
      html = 
      `
      <div class="triangle-top" style="margin: auto;"></div>
      <div class="info animated flash slower delay-5s" style="margin: auto;">${positives}</div>
      <div class="triangle-bottom" style="margin: auto;"></div>
      <div class="info animated flash slower delay-5s" style="margin: auto;">${negatives}</div>
      `;
    }

    element.innerHTML = `
    <img class="logo" style="margin: auto;" src="../images/${logo}.svg">
    <div class="stars-outer" style="margin: auto;">
      <div class="${data[dataKeys[i]].app.replace(/\s+/g, '')}-${dataKeys[i]} stars-inner" style="margin: auto;"></div>
    </div>
    <div class="nlp">
    ${html}
    </div>
    `;
    // <marquee behavior="scroll" direction="left">${sentence}</marquee>

    document.getElementsByClassName('content')[contentIndex].appendChild(element);
    // contentIndex.appendChild(element);
  }

  delay(100);

  fillStars(avgRatings);

  dataKeys.splice(0, 3);
}

async function changeSlide() {
  $('#slideshow > div:first')
      .fadeOut(1000)
      .next()
      .fadeIn(1000)
      .end()
      .appendTo('#slideshow');
}

async function workOnData(_data) {
  data = _data;
  // just... ignore this. long story.
  dataKeys = Object.keys(data);
  _dataKeys = Object.keys(data);

  for(var stuff in data) {
    sum = 0;
    count = 0;
    for(var comments in data[stuff].comments) {
      sum += data[stuff].comments[count].rating;
      count += 1;
    }

    var average = sum / count;
    if (Number.isNaN(average)) {
      average = 0;
    }
    avgRatings[stuff] = (average).toFixed(2);
  }

  avgKeys = Object.keys(avgRatings);
  console.log(data);
  console.log(dataKeys);

  for(var i=0; i<3; i++) {
    makeContent(i);
  }

  $("#slideshow > div:gt(0)").hide();

  document.addEventListener('keydown', function(event) {
    if(event.keyCode == 32) {
        changeSlide();
    }
});

  setInterval(changeSlide,  60000);
}

function fillStars() {
  const starTotal = 5;
  for(var i=0; i<3; i++) {
    const starPercentage = (avgRatings[avgKeys[i]] / starTotal) * 100;
    const starPercentageRounded = `${(Math.round(starPercentage / 10) * 10)}%`;
    var items = document.getElementsByClassName(`${data[avgKeys[i]].app.replace(/\s+/g, '')}-${dataKeys[i]} stars-inner`);
    items.item(0).style.width = starPercentageRounded;
  }
  avgKeys.splice(0, 3);
}


function reloadData() {
  $(function(){
    $.ajax({
        url: '/reload',
        data: "work",
        dataType: 'json',
        type: 'POST',
        success: function(items) {
          var _keys = Object.keys(data);
          for(var stuff in items.appsData) {
            data[_keys[stuff]].voc_coef = items.appsData[stuff].voc_coef;
          }
        }
    });
  });
}

setInterval(() => {
  reloadData();
}, 1000 * 60 * 60); 