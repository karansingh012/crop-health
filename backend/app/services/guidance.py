SOURCE='https://extension.umn.edu/agriculture/specialty-crops/vegetable-farming/disease-management/early-blight-in-tomato-and-potato'
EARLY={'symptoms':'Brown leaf spots with concentric rings, often starting on older leaves.',
       'care':'Reduce leaf wetness by watering at soil level. Improve airflow and rotate away from susceptible crops.',
       'source':SOURCE}
CATALOG={'Tomato___Early_blight':EARLY,'Potato___Early_blight':EARLY}
WARNING='Image classification is not a confirmed diagnosis. Seek qualified local advice before treatment. Weather does not prove infection.'
def guidance(label=None,crop=None,weather=None):
    entry=CATALOG.get(label,{'symptoms':'Disease-specific guidance is not available for this class.',
        'care':'Record symptoms, photograph the whole plant and affected leaves, and contact a local agricultural extension service.', 'source':None})
    context=[]
    if weather and weather.get('relative_humidity_2m',0)>=85:
        context.append('High humidity was reported. Leaf wetness may persist; this is context, not a validated disease-risk score.')
    if crop and label and not label.lower().startswith(crop.lower()):
        context.append('The selected crop and model class may not match. Request expert review.')
    return {**entry,'warnings':[WARNING]+context}
