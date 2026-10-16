function copyToClipboard(id) {
    const input = document.querySelector(`#sharevid${id} input`);
    input.select();
    document.execCommand('copy');
    
}
window.addEventListener('pageshow', function(event) {
  if (event.persisted) {
    document.body.classList.remove('page-transitioning');
    document.body.inert = false;

    const loader = document.getElementById('top-loading-bar');
    if (loader) {
      loader.style.display = 'none';
    }
  }
});

document.addEventListener('DOMContentLoaded', function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new mdb.Tooltip(tooltipTriggerEl);
    }); 
    
  
const prevUrlInput = document.getElementById('prevurl');

if (prevUrlInput) {
    try {
        const lastOrigin = sessionStorage.getItem('last_get_origin');
        prevUrlInput.value = (lastOrigin && lastOrigin.trim() !== "") ? lastOrigin : '';
    } catch (e) {
        prevUrlInput.value = ''; 
    }
}
});
(function() {
  const style = document.createElement('style');
  style.innerHTML = `
    #top-loading-bar {
      position: fixed;
      top: 0; left: 0;
      width: 0%;
      height: 4px;
      background: #007bff;
      z-index: 99999;
      transition: width 0.4s ease;
      box-shadow: 0 0 10px rgba(0, 123, 255, 0.7);
    }
    .page-transitioning {
      opacity: 0.5 !important; /* Adjust to 0 if you want it totally blank */
      pointer-events: none !important;
      cursor: wait !important;
      transition: opacity 0.4s ease;
    }
  `;
  document.head.appendChild(style);

  const loader = document.createElement('div');
  loader.id = 'top-loading-bar';
  document.body.prepend(loader);

  function startTransition() {
    document.body.classList.add('page-transitioning');
    document.body.inert = true; 
    
    loader.style.width = '30%';
    setTimeout(() => loader.style.width = '70%', 200);
    setTimeout(() => loader.style.width = '95%', 500);
  }

  document.addEventListener('submit', function(event) {
    setTimeout(() => {
      if (!event.defaultPrevented) {
        startTransition();
      }
    }, 0);
  });

  window.addEventListener('beforeunload', startTransition,

    
  );
})();
   

   
document.addEventListener('DOMContentLoaded', () => {
    try {
        const objectsToCount = document.querySelectorAll('.counthis');
        
        const displayElement = document.getElementById('countdisplay');

        if (!displayElement) {
        }else{
             const totalCount = objectsToCount.length;
        displayElement.textContent = totalCount;
        }

     

    } catch (error) {
        
       
    }
});