function folderid() {
    var url = new URL(window.location.href);
    var path = url.pathname;
    var parts = path.split("/");
    if (parts[1] === 'drive') {
        return 'root'
    }
    var val = parts[2];
    return val
}
const menu = document.getElementById("ctxMenu");

let menuVisible = false;

const toggleMenu = (command) => {
    menu.style.display = command === "show" ? "block" : "none";
    menuVisible = !menuVisible;
};

const setPosition = ({ top, left }) => {
    menu.style.left = `${left}px`;
    menu.style.top = `${top}px`;
    toggleMenu("show");
};

window.addEventListener("click", (e) => {
    if (menuVisible) toggleMenu("hide");
});

async function createFolder() {
    try {
        // Prompt the user for a folder name
        const folderName = prompt('Enter the folder name:');
        if (folderName === null) {
            return
        }

        // Create the JSON body
        const data = {
            foldername: folderName,
            file_id: folderid()
        };

        // Send the POST request
        const response = await fetch(window.location.origin + '/create_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            console.log('Folder created successfully!');
            window.location.reload();
        } else {
            console.error('Failed to create folder.');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function renamethis(item_id) {
    try {
        // Prompt the user for a folder name
        const fileName = prompt('Enter the new folder name:\n\nPlease note that filename should have extension as well.\nEg: myfile.txt');
        if (fileName === null) {
            return
        }

        // Create the JSON body
        const data = {
            filename: fileName,
            file_id: item_id
        };

        // Send the POST request
        const response = await fetch(window.location.origin + '/renamefile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            console.log('File/Folder renamed successfully!');
            window.location.reload();
        } else {
            console.error('Failed to rename file/folder.');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}


async function sharethis(item_id) {

    const jsdata = {
        file_id: item_id
    };

    // Send the POST request
    const response = await fetch(window.location.origin + '/share', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsdata)
    });

    if (response.ok) {
        console.log('File/folder shared successfully!');
        const responseData = await response.json();
        link = responseData['link']
        return link
    } else {
        console.error('Failed to share file/folder.');
    }
}

async function sharefrommenu(item_id) {
    link = await sharethis(item_id)
    bt = document.getElementById('hiddenlinksmodalbtn')
    linkspace = document.getElementById('sharedlinksplace')
    linkspace.innerText = link
    bt.click()
}


async function unsharethis(item_id) {

    const jsdata = {
        file_id: item_id
    };

    // Send the POST request
    const response = await fetch(window.location.origin + '/unshare', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsdata)
    });

    if (response.ok) {
        console.log('File/folder unshared successfully!');
        alert('Unshared the file/folder');
        window.location.reload();
    } else {
        console.error('Failed to unshare file/folder.');
    }
}


async function deletethis(item_id) {

    const jsdata = {
        file_id: item_id
    };

    // Send the POST request
    const response = await fetch(window.location.origin + '/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsdata)
    });

    if (response.ok) {
        console.log('File/folder deleted successfully!');
    } else {
        console.error('Failed to delete file/folder.');
    }
}


async function deletefrommenu(item_id) {
    await deletethis(item_id)
    window.location.reload();
}

async function starfrommenu(item_id) {
    await starthis(item_id)
    window.location.reload();
}

async function unstarfrommenu(item_id) {
    await unstarthis(item_id)
    window.location.reload();
}

async function downloadthis(item_id) {
    url = `https://drive.google.com/open?id=${item_id}`
    window.open(url, '_blank').focus();
}



async function deleteSelected() {
    try {
        const checked_boxes = [...document.querySelectorAll(".inp:checked")].map(
            (e) => e.id
        );
        if (checked_boxes.length === 0) {
            alert('No items selected.')
            return
        }
        for (const item_id of checked_boxes) {
            await deletethis(item_id);
        }
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
    }
}

async function starthis(item_id) {
    const jsdata = {
        file_id: item_id
    };

    // Send the POST request
    const response = await fetch(window.location.origin + '/addstar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsdata)
    });

    if (response.ok) {
        console.log('File/folder starred successfully!');
    } else {
        console.error('Failed to star file/folder.');
    }
}

async function starSelected() {
    try {
        const checked_boxes = [...document.querySelectorAll(".inp:checked")].map(
            (e) => e.id
        );
        if (checked_boxes.length === 0) {
            alert('No items selected.')
            return
        }
        for (const item_id of checked_boxes) {
            await starthis(item_id);
        }
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
    }
}

async function unstarthis(item_id) {

    const jsdata = {
        file_id: item_id
    };

    // Send the POST request
    const response = await fetch(window.location.origin + '/removestar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsdata)
    });

    if (response.ok) {
        console.log('File/folder unstarred successfully!');
    } else {
        console.error('Failed to unstar file/folder.');
    }
}

async function unstarSelected() {
    try {
        const checked_boxes = [...document.querySelectorAll(".inp:checked")].map(
            (e) => e.id
        );
        if (checked_boxes.length === 0) {
            alert('No items selected.')
            return
        }
        for (const item_id of checked_boxes) {
            await unstarthis(item_id);
        }
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
    }
}



['dragleave', 'drop', 'dragenter', 'dragover'].forEach(function (evt) {
    document.addEventListener(evt, function (e) {
        e.preventDefault();
    }, false);
});


function generateRandomString(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;

    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }

    return result;
}
// var drop_area = document.getElementById('drop_area');
var drop_area = document.body

function showuploadmodal(){
    let m = document.getElementById('exampleModal');
    m.classList.add('show');
    m.style.display='block';
    m.removeAttribute('aria-hidden');
    m.setAttribute('aria-modal','true');
    m.setAttribute('role','dialog');
    document.body.style.overflow='hidden';
    document.body.style.paddingRight='17px'
    document.body.classList.add('modal-open');
    ele = document.createElement('div');
    ele.setAttribute('id','theexplicitshow')
    ele.classList.add('modal-backdrop')
    ele.classList.add('fade')
    ele.classList.add('show')
    document.body.appendChild(ele)
}


function hideuploadmodal(){
    let m = document.getElementById('exampleModal');
    m.classList.remove('show');
    m.style.display='none';
    m.setAttribute('aria-hidden','true');
    m.removeAttribute('aria-modal');
    m.removeAttribute('role');
    document.body.style.removeProperty('overflow')
    document.body.style.removeProperty('paddingRight')
    document.body.classList.remove('modal-open');
    ele = document.getElementById('theexplicitshow');
    ele.remove()
}


async function processItems(items, path) {
    let fl_ls = [];
    let file_paths = [];

    for (let i = 0; i < items.length; i++) {
        var item = items[i];
        var entry = item.webkitGetAsEntry();

        if (entry.isDirectory) {
            await processDirectory(entry, path + entry.name + '/', fl_ls, file_paths);
        }
        if ((entry.isFile)) {
            // console.log(entry.name)
            let file = item.getAsFile();
            // let file = item.getAsFile();
            fl_ls.push(file);
            file_paths.push(path + file.name);
        }

    }
    return [fl_ls, file_paths]
}

async function processDirectory(directory, path, fl_ls, file_paths) {
    let dirReader = directory.createReader();
    let entries = await readEntriesAsync(dirReader);

    for (let i = 0; i < entries.length; i++) {
        entry = entries[i]
        if (entry.isDirectory) {
            await processDirectory(entry, path + entry.name + '/', fl_ls, file_paths);
        } else {
            let file = await getFileAsync(entry);
            fl_ls.push(file);
            file_paths.push(path + file.name);
        }
    }
}

function readEntriesAsync(dirReader) {
    return new Promise((resolve, reject) => {
        dirReader.readEntries(
            (entries) => resolve(entries),
            (error) => reject(error)
        );
    });
}

function getFileAsync(entry) {
    return new Promise((resolve, reject) => {
        entry.file(
            (file) => resolve(file),
            (error) => reject(error)
        );
    });
}

function drag_over(event) { 
    event.preventDefault(); 
    document.getElementById('upload-dialog-drag').style.display = "block";
    return false; 
} 

drop_area.addEventListener('drop', async function (e) {
    e.preventDefault();
    document.getElementById('upload-dialog-drag').style.display = "none";
    showuploadmodal();
    var fileList = e.dataTransfer.items; // the files to be uploaded
    // console.log(fileList)
    var fileList2 = e.dataTransfer.files; // the files to be uploaded
    if (fileList.length == 0 || fileList2.length == 0) {
        hideuploadmodal();
        return false;
    }
    ulnum = generateRandomString(32)

    // we use XMLHttpRequest here instead of fetch, because with the former we can easily implement progress and speed.
    var xhr = new XMLHttpRequest();
    xhr.open('post', window.location.origin + '/upload', true); // aussume that the url /upload handles uploading.
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // uploading is successful
            alert('Successfully uploaded!');  // please replace with your own logic
            window.location.reload();
        }
    };

    // show uploading progress
    var lastTime = Date.now();
    var lastLoad = 0;
    xhr.upload.onprogress = function (event) {
        if (event.lengthComputable) {
            // update progress
            var percent = Math.floor(event.loaded / event.total * 100);
            document.getElementById('upload_progress').innerHTML = 'Processing Progress ' + percent + ' %';

            // update speed
            var curTime = Date.now();
            var curLoad = event.loaded;
            var speed = ((curLoad - lastLoad) / (curTime - lastTime) / 1024).toFixed(2);
            document.getElementById('speed').innerHTML = 'Processing Speed ' + speed + ' MB/s'
            lastTime = curTime;
            lastLoad = curLoad;
        }
    };

    // send files to server
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    var fd = new FormData();

    dropped_folder_ls = []
    dropped_files_ls = []

    for (i = 0; i < fileList.length; i++) {
        f = fileList[i]
        tmp = f.webkitGetAsEntry();
        if (tmp.isDirectory) {
            dropped_folder_ls.push([f]);
        }
        else {
            dropped_files_ls.push([f]);
        }
    }

    let files = [];
    let file_paths = [];

    let make_upload = false;
    if ((dropped_files_ls.length !== 0 && dropped_folder_ls.length === 0) || (dropped_files_ls.length === 0 && dropped_folder_ls.length === 1)) {
        make_upload = true;
    }

    if (!make_upload) {
        hideuploadmodal();
        document.getElementById('hiddenuploadinfobtn').click()
        return false;
    }

    let is_folder = "false";
    console.log(dropped_folder_ls.length)

    if (dropped_folder_ls.length === 1) {
        is_folder = "true";
    }
    else if (dropped_folder_ls.length === 0) {
        is_folder = "false";
    }


    for (let folder of dropped_folder_ls) {
        let [f_ls, fpath_ls] = await processItems(folder, '');
        files.push(...f_ls);
        file_paths.push(...fpath_ls);
    }

    for (let file of dropped_files_ls) {
        let [f_ls, fpath_ls] = await processItems(file, '');
        files.push(...f_ls);
        file_paths.push(...fpath_ls);
    }

    for (let file of files) {
        fd.append('files', file);
    }
    lastTime = Date.now();
    fd.append('file_paths', JSON.stringify(file_paths))
    fd.append('ulnum', ulnum)
    fd.append('is_folder', is_folder)
    fd.append('parent_id', folderid())
    xhr.send(fd);
    // setInterval(function () {
    //     var progressXhr = new XMLHttpRequest();
    //     progressXhr.open('POST', window.location.origin + '/get_progress', true); // assume that the URL /get_progress returns progress data.
    //     progressXhr.setRequestHeader('Content-Type', 'application/json');

    //     progressXhr.onreadystatechange = function () {
    //         if (progressXhr.readyState == 4 && progressXhr.status == 200) {
    //             var progress = JSON.parse(progressXhr.responseText);
    //             console.log(progress)
    //             if (progress !== {}) {
    //                 // update the progress div
    //                 for (let key in progress) {
    //                     console.log();
    //                     document.getElementById('progress_div').innerText = key + " - " + progress[key];
    //                     if (parseInt(progress[key]) === 100) {
    //                         clearInterval(this); // stop the interval when upload is complete
    //                     }
    //                 }


    //                 // check if upload is complete

    //             }
    //         }
    //     };

    //     // send ulnum as JSON body
    //     progressXhr.send(JSON.stringify({ 'ulnum': ulnum }));
    // }, 5000);
}, false);

drop_area.addEventListener('dragover',drag_over,false); 

function rightclickctxmenu(e, file_id) {
    e.preventDefault();
    menu.dataset.id = file_id
    console.log(menu)
    const origin = {
        left: e.pageX,
        top: e.pageY,
    };
    setPosition(origin);
    return false;
}


// window.addEventListener("contextmenu", (e) => {
//     e.preventDefault();
//     const origin = {
//         left: e.pageX,
//         top: e.pageY,
//     };
//     setPosition(origin);
//     return false;
// });

