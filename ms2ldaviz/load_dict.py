import os
import pickle
import numpy as np
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ms2ldaviz.settings")

import django
django.setup()

import jsonpickle

from basicviz.models import Experiment,Document,Feature,FeatureInstance,Mass2Motif,Mass2MotifInstance,DocumentMass2Motif,FeatureMass2MotifInstance,Alpha

def add_all_features(experiment,features):
    # Used when we have a dictionary of features with their min and max mz values
    nfeatures = len(features)
    ndone = 0
    for feature in features:
        mz_vals = features[feature]
        f = add_feature(feature,experiment)
        f.min_mz = mz_vals[0]
        f.max_mz = mz_vals[1]
        f.save()
        ndone += 1
        if ndone % 100 == 0:
            print "Done {} of {}".format(ndone,nfeatures)


def add_document(name,experiment,metadata):
    d = Document.objects.get_or_create(name = name,experiment = experiment,metadata = metadata)[0]
    return d

def add_feature(name,experiment):
    try:
        f = Feature.objects.get_or_create(name = name,experiment = experiment)[0]
    except:
        print name,experiment
        sys.exit(0)
    return f

def add_feature_instance(document,feature,intensity):
    try:
        fi = FeatureInstance.objects.get_or_create(document=document,feature=feature,intensity=intensity)[0]
    except:
        print document,feature,intensity
        sys.exit(0)


def add_topic(topic,experiment,metadata,lda_dict):
    m2m = Mass2Motif.objects.get_or_create(name = topic,experiment = experiment,metadata = metadata)[0]
    for word in lda_dict['beta'][topic]:
        feature = Feature.objects.get(name = word,experiment=experiment)
        Mass2MotifInstance.objects.get_or_create(feature = feature,mass2motif = m2m,probability = lda_dict['beta'][topic][word])[0]
    topic_pos = lda_dict['topic_index'][topic]
    alp = Alpha.objects.get_or_create(mass2motif = m2m,value = lda_dict['alpha'][topic_pos])

def add_theta(doc_name,experiment,lda_dict):
    document = Document.objects.get(name = doc_name,experiment=experiment)
    for topic in lda_dict['theta'][doc_name]:
        mass2motif = Mass2Motif.objects.get(name = topic,experiment = experiment)
        DocumentMass2Motif.objects.get_or_create(document = document,mass2motif = mass2motif,probability = lda_dict['theta'][doc_name][topic])[0]

def load_phi(doc_name,experiment,lda_dict):
    document = Document.objects.get(name = doc_name,experiment=experiment)
    for word in lda_dict['phi'][doc_name]:
        feature = Feature.objects.get(name=word,experiment=experiment)
        feature_instance = FeatureInstance.objects.get(document=document,feature=feature)
        for topic in lda_dict['phi'][doc_name][word]:
            mass2motif = Mass2Motif.objects.get(name=topic,experiment=experiment)
            probability = lda_dict['phi'][doc_name][word][topic]
            FeatureMass2MotifInstance.objects.get_or_create(featureinstance = feature_instance,mass2motif = mass2motif,probability = probability)[0]

def add_document_words(document,doc_name,experiment,lda_dict):
    for word in lda_dict['corpus'][doc_name]:
        feature = add_feature(word,experiment)
        # feature = Feature.objects.get_or_create(name=word,experiment=experiment)[0]
        # fi = FeatureInstance.objects.get_or_create(document = d,feature = feature, intensity = lda_dict['corpus'][doc][word])
        add_feature_instance(document,feature,lda_dict['corpus'][doc_name][word])

def load_dict(lda_dict,experiment,verbose = True):
    if 'features' in lda_dict:
        print "Explicit feature object: loading them all at once"
        add_all_features(experiment,lda_dict['features'])

    print "Loading corpus"
    n_done = 0
    to_do = len(lda_dict['corpus'])
    for doc in lda_dict['corpus']:
        n_done += 1
        if n_done % 100 == 0:
            print "Done {}/{}".format(n_done,to_do)
            experiment.status = "Done {}/{} docs".format(n_done,to_do)
            experiment.save()
        metdat = jsonpickle.encode(lda_dict['doc_metadata'][doc])
        if verbose:
            print doc,experiment,metdat
        d = add_document(doc,experiment,metdat)
        # d = Document.objects.get_or_create(name=doc,experiment=experiment,metadata=metdat)[0]
        add_document_words(d,doc,experiment,lda_dict)



        # for word in lda_dict['corpus'][doc]:
        #   feature = add_feature(word,experiment)
        #   # feature = Feature.objects.get_or_create(name=word,experiment=experiment)[0]
        #   # fi = FeatureInstance.objects.get_or_create(document = d,feature = feature, intensity = lda_dict['corpus'][doc][word])
        #   add_feature_instance(d,feature,lda_dict['corpus'][doc][word])
    print "Loading topics"
    n_done = 0
    to_do = len(lda_dict['beta'])
    for topic in lda_dict['beta']:
        n_done += 1
        if n_done % 100 == 0:
            print "Done {}/{}".format(n_done,to_do)
            experiment.status = "Done {}/{} topics".format(n_done,to_do)
            experiment.save()
        metadata = {}
        metadata = lda_dict['topic_metadata'].get(topic,{})
        add_topic(topic,experiment,jsonpickle.encode(metadata),lda_dict)

        # m2m = Mass2Motif.objects.get_or_create(name = topic,experiment = experiment,metadata = jsonpickle.encode(metadata))[0]
        # for word in lda_dict['beta'][topic]:
        #   feature = Feature.objects.get(name = word,experiment=experiment)
        #   Mass2MotifInstance.objects.get_or_create(feature = feature,mass2motif = m2m,probability = lda_dict['beta'][topic][word])

    print "Loading theta"
    n_done = 0
    to_do = len(lda_dict['theta'])
    for doc in lda_dict['theta']:
        n_done += 1
        if n_done % 100 == 0:
            print "Done {}/{}".format(n_done,to_do) 
            experiment.status = "Done {}/{} theta".format(n_done,to_do)     
            experiment.save()
        add_theta(doc,experiment,lda_dict)


        # document = Document.objects.get(name = doc,experiment=experiment)
        # for topic in lda_dict['theta'][doc]:
        #   mass2motif = Mass2Motif.objects.get(name = topic,experiment = experiment)
        #   DocumentMass2Motif.objects.get_or_create(document = document,mass2motif = mass2motif,probability = lda_dict['theta'][doc][topic])

    print "Loading phi"
    n_done = 0
    to_do = len(lda_dict['phi'])
    for doc in lda_dict['phi']:
        n_done += 1
        if n_done % 100 == 0:
            print "Done {}/{}".format(n_done,to_do)
            experiment.status = "Done {}/{} phi".format(n_done,to_do)
            experiment.save()
        load_phi(doc,experiment,lda_dict)
        # document = Document.objects.get(name = doc,experiment=experiment)
        # for word in lda_dict['phi'][doc]:
        #   feature = Feature.objects.get(name=word,experiment=experiment)
        #   feature_instance = FeatureInstance.objects.get(document=document,feature=feature)
        #   for topic in lda_dict['phi'][doc][word]:
        #       mass2motif = Mass2Motif.objects.get(name=topic,experiment=experiment)
        #       probability = lda_dict['phi'][doc][word][topic]
        #       FeatureMass2MotifInstance.objects.get_or_create(featureinstance = feature_instance,mass2motif = mass2motif,probability = probability)

if __name__ == '__main__':

    filename = sys.argv[1]
    verbose = False
    if 'verbose' in sys.argv:
        verbose = True
    with open(filename,'r') as f:
        lda_dict = pickle.load(f)
    experiment_name = filename.split('/')[-1].split('.')[0]
    current_e = Experiment.objects.filter(name = experiment_name)
    if len(current_e) > 0:
        print "Experiment of this name already exists, exiting"
        sys.exit(0)

    experiment = Experiment(name = experiment_name)
    experiment.status = 'loading'
    experiment.save()

    load_dict(lda_dict,experiment,verbose)
