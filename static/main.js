/**
 * Constants
 * 
 */
var slidesPerView = 6;
var CHUNK_SIZE = 1024;

/**
 * Globals
 * 
 */
var map = null;
var csvFile = null;
var currentLatLng = null;
var swiper = null;
var folders = [];

var selected = null;

 /**
  * Inactivate the Tabs
  */
 function inactivateTabs() {
  var iTab, tabcontent, tabbuttons, tablinks;
   
   // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (iTab = 0; iTab < tabcontent.length; iTab++) {
      tabcontent[iTab].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (iTab = 0; iTab < tablinks.length; iTab++) {
      tablinks[iTab].className = tablinks[iTab].className.replace(" active", "");
      tablinks[iTab].style.textDecoration = "none";
  }

}

/**
* Show the Active Tab
* 
* @param {event} evt the Tab to Show
* @param {string} tab the name of the Tab
* @param {string} button the Tab's button
*/
function showTab(evt, tab, button) {

  inactivateTabs();

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tab).style.display = "block";
  document.getElementById(button).style.textDecoration = "underline";

  evt.currentTarget.className += " active";

}

/**
 * Create a swiper control
 * @return the newly constructed swiper control
 */
function createSwipperControl() {

  var swiper = new Swiper('.swiper-container', {
    slidesPerView: slidesPerView,
    centeredSlides: false,
    spaceBetween: 10,
    breakpointsInverse: true,
    breakpoints: {
      200: {
        slidesPerView: 1,
        spaceBetween: 10
      },
      600: {
        slidesPerView: 2,
        spaceBetween: 10
      },    
      800: {
        slidesPerView: 3,
        spaceBetween: 10
      },    
      1000: {
        slidesPerView: 4,
        spaceBetween: 10
      },
      1200: {
        slidesPerView: 5,
        spaceBetween: 10
      },    
      1400: {
        slidesPerView: 6,
        spaceBetween: 10
      },   
      1600: {
        slidesPerView: 7,
        spaceBetween: 10
      },
      1800: {
        slidesPerView: 8,
        spaceBetween: 10
      },
      2000: {
        slidesPerView: 9,
        spaceBetween: 10
      },   
      2200: {
       slidesPerView: 10,
        spaceBetween: 11
      }
    },
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },

  });

  return swiper;

}

/**
 * Generate a Card
 * @param {*} fileName the Name of the File
 */
function generateCard(fileName) {
    var slide = 
    `<div class='swiper-slide' style='border:2px solid #0174DF; background-color: rgba(255,255,255, 0.30);' onclick='processImage(` +
    `"${fileName}");'> ` + 
        "<div style='position:absolute; left:3px; top:5px; right:3px;'>" +
        "<div class='play'>" + 
            `<img src='${playImage}' style='width:64px; height:64px; margin-top:130px;'/>` +
            "</div>" +
        "</div>" +
        "<table style='color:rgba(0,0,0,0.8); font-family: monospace; font-size: 12px;'>" +
            "<tr><td><label style='position:relative;  display: inline-block; color:rgba(0,0,0,0.8); width:180px; font-family: monospace; " +
            "text-overflow: ellipsis; overflow:hidden; white-space:nowrap; font-size:14px; font-weight:bold'>" +
            fileName + 
        "</label></td>" +  
        "</tr>" + 
        "</table>" +
        "</div>" +
    "</div>";

    return slide;

}

/**
* Show the Active Tab
* @param {string} filename the Image's file name
*/
function processImage(filename) {

    console.log("Processing Image");

    $('#waitDialog').css('display', 'inline-block');

    var request = new XMLHttpRequest();

    request.open("GET", encodeURI("/process?filename=" + filename), true);
    request.responseType = "arraybuffer";
    
    request.onload = function(oEvent) {
      var arrayBuffer = request.response;
  
      var byteArray = new Uint8Array(arrayBuffer);

      // If you want to use the image in your DOM:
      var blob = new Blob([arrayBuffer], {type: "image/png"});
      var url = URL.createObjectURL(blob);
 
      $("#imageContent").attr("src", url);
    
      $('#display').css('display', 'inline-block');
      $('#imageFrame').css('display', 'inline-block');
      $('#waitDialog').css('display', 'none');

    };
    
    request.send();

}

function generateSwiperEntries(data) {
    var entries = JSON.parse(data);
    var html = "";  
        
    for (entry in entries) {
        html += generateCard(entries[entry].file_name);
    }       

    return html;

}

function setupDisplay() {

    $('#waitDialog').css('display', 'inline-block');

    $.get('/list', {}, function(data) {
        var entries = JSON.parse(data);
        
        $('#swiper-wrapper').html(generateSwiperEntries(data));
    
        $('#swiper-container').css('visibility', 'visible');
    
        swiper = createSwipperControl();
    
        $('#swiper-container').css('visibility', 'visible');

        $('#waitDialog').css('display', 'none');

    });

}

function refreshView(callback) {

    $('#waitDialog').css('display', 'inline-block');

    $.get('/list', {}, function(data) {     
        var entries = JSON.parse(data);

        $('#swiper-wrapper').html(generateSwiperEntries(data));
        
        swiper.update();
        
        callback();

        $('#waitDialog').css('display', 'none');  

    });

}

$(document).ready(function() {

    $('#refresh').bind('click', (e) => {
        
        refreshView(function() {

        });

    });

    setupDisplay();

    var dropzone = $('#droparea');

    dropzone.on('dragover', function() {
        dropzone.addClass('hover');
        return false;
    });

    dropzone.on('dragleave', function() {
        dropzone.removeClass('hover');
        return false;
    });
    
    dropzone.on('drop', function(e) {
        e.stopPropagation();
        e.preventDefault();
        dropzone.removeClass('hover');
    
        //retrieve uploaded files data
        var files = e.originalEvent.dataTransfer.files;
        processFiles(files);
        
        return false;

    });
    
    var uploadBtn = $('#uploadbtn');
    var defaultUploadBtn = $('#upload');
    
    uploadBtn.on('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        defaultUploadBtn.click();
    });

    defaultUploadBtn.on('change', function() {
        var files = $(this)[0].files;

        processFiles(files);

        return false;

    });  

    /**
     * Process uploaded files
     * 
     * @param {file[]} files an array of files
     * 
     */
    function processFiles(files) {
        var reader = new FileReader();

        reader.onload = function() {
            var arrayBuffer = reader.result;
    
            console.log(`Chunking: ${files[0].name}`);
            chunkData(files[0].name, arrayBuffer);
            
        };

        reader.readAsArrayBuffer(files[0]);
        
    }

    function chunkData(filename, data) {
        var maxChunks = (Math.floor(data.byteLength / CHUNK_SIZE)) + ((data.byteLength % CHUNK_SIZE == 0) ? 0 : 1);

        $('#waitDialog').css('display', 'inline-block');
        $('#waitMessage').text('Chunking Data : ' + data.byteLength);
        console.log(`Chunking Data : ${data.byteLength} : ${maxChunks}`);
        
        sendData(filename, data, maxChunks).then(function(result) {
            
            if (result.status != 'OK') {
                
                $('#waitMessage').text('');
                $('#waitDialog').css('display', 'none');
    
                return;
            }

            var guid = result.guid;
            var tempFilename = result.tempFilename;

            $('#waitMessage').text(`Committing : '${filename}' - Length: ${data.byteLength}`);
 
            var parameters = {filename: filename,
                              filelength: `${data.byteLength}`};

            $.get('/commit', parameters, function(result) {
                $('#waitMessage').text('Processing : ' + filename);
 
                $.get('/process', parameters, function(result) {

                    refreshView(function() {
                        $('#waitMessage').text('');
                        $('#waitDialog').css('display', 'none');
                    });    

                }).fail(function(code, err) {
                    alert(err); 
                    $('#waitMessage').text('');
                    $('#waitDialog').css('display', 'none');
        
                });

            }).fail(function(code, err) {
                alert(err); 
                $('#waitMessage').text('');
                $('#waitDialog').css('display', 'none');

            });

        });

    }

    /**
     * Send the Data to the Server in Chunks
     * 
     * @param {string} filename Video's Filename
     * @param {ArrayBuffer} data the Video Content
     * @param {integer} maxChunks Number of Posts to deliver the Video
     * 
     */
    async function sendData(filename, data, maxChunks) {
        var currentChunk = 0;
        var guid = '';
        var tempFilename = '';

        console.log(`sendData: ${filename} - ${data.byteLength}`);
        var position = 0;

        for (var iChunk=0; iChunk < maxChunks; iChunk += 1) {   
            var chunk = data.slice(iChunk * CHUNK_SIZE, (iChunk + 1) * CHUNK_SIZE); 

            console.log(`Posting: ${filename} : ${chunk.byteLength}`);

            var result = await postData(filename, chunk, position, currentChunk, maxChunks);

            position += chunk.byteLength;

            console.log(`Uploaded  - [${currentChunk}/${maxChunks}] : + '${filename} : ${position}`);

            currentChunk += 1;
        
        }

        return {
            status: 'OK'
        }

    }

    /**
     * Post the Data to the Server in Chunks
     * 
     * @param {string} filename Filename
     * @param {ArrayBuffer} chunk the Video Content
     * @param {integer} position Current Position
     * @param {integer} currentChunk Current Chunk Index
     * @param {integer} maxChunks Number of Posts to deliver the Data
     * 
     */
    function postData(filename, chunk, position, currentChunk, maxChunks) {    
        var content = null;
        
        console.log(`Posting Data: ${filename}`);
    
        try {
            content = new File([chunk], filename);
        } catch (e) {
            content = new Blob([chunk], filename); 
        }

        var formData = new FormData();

        formData.append('filename', filename);   
        formData.append('chunk', `${currentChunk}`);
        formData.append('position', `${position}`);
        formData.append('maxChunks', `${maxChunks}`);
 
        formData.append(filename, content);

        return new Promise(resolve => {$.ajax({
            url: '/upload',
            type: 'POST',
            maxChunkSize: CHUNK_SIZE,
            contentType: false,
            processData: false,
            async: true,
            data: formData,
                xhr: function() {
                    var xhr = $.ajaxSettings.xhr();

                    xhr.upload.addEventListener('progress', function (event) {
                        if (event.lengthComputable) {
                            var percentComplete = event.loaded / event.total;                          }
                    }, false);

                    xhr.upload.addEventListener('load', function (event) {
                    }, false);

                    return xhr;

                },
                error: function (err) {
                    console.log(`Error: [${err.status }] - ' ${err.statusText}'`); 
                    alert(`Error: [${err.status }] - ' ${err.statusText}'`);
                    resolve(err);

                },
                success: function (result) {  
                    $('#waitMessage').text(`Sending  - ${currentChunk}/${maxChunks} - ${position}`);
                    console.log(`Resolved: ${result}`);
                    resolve(JSON.parse(result));

                }
            });

        });

    }

});
