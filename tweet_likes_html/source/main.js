let currentPage = 1
let totalPages = Math.ceil(tweets.length / tweetsPerPage);
function getTextWidth() {
    const userHandles = document.querySelectorAll('.tweet_author_handle');
    const userNames = document.querySelectorAll('.tweet_author_name');
    for (let i = 0; i < userHandles.length; i++) {
        if (userHandles[i].querySelector('a').getBoundingClientRect().width >= 240) {
            userHandles[i].style.width = "240px";
        } else {
            userHandles[i].style.width = "auto";
        }
    }
    for (let i = 0; i < userNames.length; i++) {
        if (userNames[i].querySelector('a').getBoundingClientRect().width >= 240) {
            userNames[i].style.width = "240px";
        } else {
            userNames[i].style.width = "auto";
        }
    }
}

function displayPage(pageNumber){
    currentPage = pageNumber
    const startIndex = (pageNumber - 1) * tweetsPerPage;
    const endIndex = pageNumber * tweetsPerPage;
    const tweetsDataForPage = tweets.slice(startIndex, endIndex);
    tweetsContainer.innerHTML = '';
    tweetsDataForPage.forEach(tweet => {
        tweetsContainer.innerHTML += tweet;
    });
    
    getTextWidth()
    
    var msnry = new Masonry( 
        tweetsContainer, 
        {itemSelector: '.tweet_wrapper', fitWidth: fitWidth});
    
    var imgLoad = imagesLoaded('#tweet_list');
    imgLoad.on('progress', ()=>{
    	msnry.layout()
    });
    window.scrollTo({top: 0, behavior: 'smooth'});
    updatePageButtons()
}

function updatePageButtons() {
    document.getElementById('current-page').textContent = `${currentPage} - ${totalPages}`;
    document.getElementById('prev-page').setAttribute('disabled', currentPage === 1);
    document.getElementById('next-page').setAttribute('disabled', currentPage === totalPages);
    document.getElementById('first-page').setAttribute('disabled', currentPage === 1);
    document.getElementById('last-page').setAttribute('disabled', currentPage === totalPages);
}

document.getElementById('first-page').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage = 1;
        displayPage(currentPage);
    }
});

document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        displayPage(currentPage);
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    if (currentPage < totalPages) {
        currentPage++;
        displayPage(currentPage);
    }
});

document.getElementById('last-page').addEventListener('click', () => {
    if (currentPage < totalPages) {
        currentPage = totalPages;
        displayPage(currentPage);
    }
});

tweetsContainer = document.querySelector('#tweet_list')
tweetsContainer.setAttribute('fitwidth', fitWidth)
window.onload = ()=>{displayPage(1);};
window.addEventListener("resize", getTextWidth);
updatePageButtons();