const ROOT=import.meta.env.VITE_API_URL||'/api';
export async function api(path,options={}){
 const headers={...options.headers};
 const token=sessionStorage.getItem('canopy-token');
 if(token)headers.Authorization=`Bearer ${token}`;
 if(options.body&&!(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}
 const response=await fetch(ROOT+path,{...options,headers});
 if(!response.ok){let data;try{data=await response.json()}catch{data={detail:response.status===429?'Too many requests. Please wait a moment and try again.':'Service unavailable'}}
 if(response.status===401&&token){sessionStorage.removeItem('canopy-token');window.dispatchEvent(new Event('session-expired'));}
 throw Error(typeof data.detail==='string'?data.detail:'Please check the form values.');}
 if(options.blob)return response.blob();
 return response.status===204?null:response.json();
}
export async function downloadReport(id){const blob=await api(`/scans/${id}/report?language=${localStorage.getItem('canopy-language')==='hi'?'hi':'en'}`,{blob:true});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`canopy-scan-${id}.pdf`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
