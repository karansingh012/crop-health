import os
import httpx
from fastapi import HTTPException
async def weather_at(latitude,longitude):
    if os.getenv('WEATHER_ENABLED','true').lower()!='true':
        raise HTTPException(503,'Weather is disabled. Configure WEATHER_ENABLED=true.')
    key=os.getenv('OPEN_METEO_API_KEY')
    host='https://customer-api.open-meteo.com/v1/forecast' if key else 'https://api.open-meteo.com/v1/forecast'
    params={'latitude':latitude,'longitude':longitude,'current':'temperature_2m,relative_humidity_2m,precipitation','timezone':'UTC'}
    if key: params['apikey']=key
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.get(host,params=params)
            response.raise_for_status()
            data=response.json()
        return {'current':data['current'],'units':data['current_units'],'source':'Open-Meteo','source_url':'https://open-meteo.com/','note':'Weather model estimate; not an infection diagnosis.'}
    except (httpx.HTTPError,ValueError,KeyError):
        raise HTTPException(502,'Weather provider unavailable; try again later')

async def search_places(name,language='en'):
    """Return disambiguated place choices; never silently choose a same-named town."""
    key=os.getenv('OPEN_METEO_API_KEY')
    host='https://customer-geocoding-api.open-meteo.com/v1/search' if key else 'https://geocoding-api.open-meteo.com/v1/search'
    params={'name':name.strip(),'count':8,'language':language,'format':'json'}
    if key:params['apikey']=key
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response=await client.get(host,params=params);response.raise_for_status();data=response.json()
        return [{'id':p['id'],'name':p['name'],'region':p.get('admin1',''),'country':p.get('country',''),
                 'latitude':p['latitude'],'longitude':p['longitude']} for p in data.get('results',[])]
    except (httpx.HTTPError,ValueError,KeyError):
        raise HTTPException(502,'Location search is unavailable. Try again or use your device location.')
