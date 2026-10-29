import classHindi from '../../shared/class-hi.json';
const {crops,diseases}=classHindi;
import React,{useSyncExternalStore,useEffect} from 'react';
import hindi from '../../shared/hi.json';
let language=localStorage.getItem('canopy-language')==='hi'?'hi':'en';
const listeners=new Set();
const subscribe=listener=>{listeners.add(listener);return()=>listeners.delete(listener)};
export function useLanguage(){const value=useSyncExternalStore(subscribe,()=>language);useEffect(()=>{document.documentElement.lang=value},[value]);return value}
export function setLanguage(next){language=next==='hi'?'hi':'en';localStorage.setItem('canopy-language',language);listeners.forEach(listener=>listener())}
export function t(message,values={}){if(message==null)return '';const text=language==='hi'?(hindi[message]||message):message;return String(text).replace(/\{(\w+)\}/g,(match,key)=>values[key]??match)}
export function LanguageSwitch(){const current=useLanguage();return <select className="language-select" aria-label="Language / भाषा" value={current} onChange={event=>setLanguage(event.target.value)}><option value="en">English</option><option value="hi">हिन्दी</option></select>}


export function translateClass(value){if(!value)return t('No prediction');if(!value.includes('___'))return t(value.replaceAll('_',' '));const [crop,disease]=value.split('___');if(language==='en')return `${crop.replaceAll('_',' ')} · ${disease.replaceAll('_',' ')}`;const name=Object.keys(crops).find(key=>crop.startsWith(key));return `${crops[name]||crop.replaceAll('_',' ')} · ${diseases[disease]||disease.replaceAll('_',' ')}`}
