#!/bin/env python
import datasets
from adapters import AutoAdapterModel, AdapterConfig, AdapterTrainer
from transformers import TrainingArguments, EvalPrediction, AutoTokenizer
from transformers import pipeline
import torch
import os
import sys
from pathlib import Path

import numpy as np

os.environ["WANDB_DISABLED"] = "true"

device = "cuda" if torch.cuda.is_available() else "cpu"

task = "dact"
anno_type = 'with_context'
# "without_context_with_current_speaker"
# valid annotation types:
# without_context_and_without_speaker
# without_context_with_current_speaker
# with_context_with_current_and_previous_speaker
# with_context
# iso
# iso_simplified
# summary
# low_resource_turn_and_speaker

batch_size = 16#32
model_name = "bert-base-german-cased"

data_folder = "csv_da_annotations/csv" + (
    "_with_context_with_current_and_previous_speaker"
    if anno_type.startswith('with') else anno_type)

low_resource_annotation_prefix = ""
# valid low-resource annotation types:
# "" corresponds to the baseline (no data augmentation)
# backtranslated_
# backtranslated_with_fr_
# (masked|random)_(0.1|0.2|0.4|0.6)_(1|2|5|10)_
# e.g.: "masked_0.2_5_"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoAdapterModel.from_pretrained(model_name)

if anno_type=="iso":
    label2id = {"Answer":0, "Disconfirm":1, "Inform":2, "Request":3, "Offer":4, "Confirm":5, "Auto-positive":6, "TurnAccept":7, "Question":8, "TurnAssign":9, "PropositionalQuestion":10, "Agreement":11, "Promise":12, "TurnTake":13, "AddressRequest":14, "AcceptOffer":15, "AcceptRequest":16, "Pausing":17, "CheckQuestion":18, "DeclineOffer":19, "Auto-negative":20, "SetQuestion":21, "ChoiceQuestion":22, "Instruct":23, "Allo-positive":24, "Other":25}
else:
    label2id = {"Absage":0, "Einsatzbefehl":1, "Information_geben":2, "Information_nachfragen":3, "Kontakt_Anfrage":4, "Kontakt_Bestaetigung":5, "Sonstiges":6, "Zusage":7}
id2label = dict()
for k,v in label2id.items():
    id2label[v] = k

def build_intext(data):
    encoded = None
    if anno_type=="without_context_and_without_speaker":
        encoded = [doc for doc in data["tokens"]]
    elif anno_type=="without_context_with_current_speaker" or anno_type=="low_resource_turn_and_speaker":
        encoded = [data["speakers"][doc_i]+" [SEP] "+ doc_tokens for doc_i, doc_tokens in enumerate(data["tokens"])]
    elif anno_type=="with_context_with_current_and_previous_speaker":
        encoded = [data["previous_speakers"][doc_i]+" [SEP] "+data["previous"][doc_i]+" [SEP] "+data["speakers"][doc_i]+" [SEP] "+doc_tokens for doc_i, doc_tokens in enumerate(data["tokens"])]
    elif anno_type=="with_context":
        encoded = [data["previous"][doc_i]+" [SEP] " + doc_tokens for doc_i, doc_tokens in enumerate(data["tokens"])]
    elif anno_type=="iso_simplified" or anno_type=="iso":
        encoded = [data["speakers"][doc_i]+" [SEP] "+data["isoda"][doc_i]+" [SEP] "+doc_tokens for doc_i, doc_tokens in enumerate(data["tokens"])]
    elif anno_type=="summary":
        encoded = [truncate_summary(data["summary"][doc_i])+" [SEP] "+data["speakers"][doc_i]+" [SEP] "+doc_tokens for doc_i, doc_tokens in enumerate(data["tokens"])]
    return encoded

def encode_data(data):
    encoded = None
    if anno_type=="without_context_and_without_speaker":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=128, truncation=True, add_special_tokens=True)
    elif anno_type=="without_context_with_current_speaker" or anno_type=="low_resource_turn_and_speaker":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=256, truncation=True, add_special_tokens=True)
    elif anno_type=="with_context_with_current_and_previous_speaker":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=256, truncation=True, add_special_tokens=True)
    elif anno_type=="with_context":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=256, truncation=True, add_special_tokens=True)
    elif anno_type=="iso_simplified" or anno_type=="iso":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=256, truncation=True, add_special_tokens=True)
    elif anno_type=="summary":
        encoded = tokenizer(build_intext(data), pad_to_max_length=True, padding="max_length", max_length=512, truncation=True, add_special_tokens=True)
    return encoded


def compute_accuracy(p: EvalPrediction):
    preds = np.argmax(p.predictions, axis=1)
    return {"acc": (preds == p.label_ids).mean()}

def compute_f1(p: EvalPrediction):
    preds = np.argmax(p.predictions, axis=1)
    tp = 0
    fn = 0
    fp = 0
    for i in range(len(preds)):
        predicted = preds[i]
        gold = p.label_ids[i]
        if gold==predicted:
            tp+=1
        elif gold!=predicted and gold==1:
            fn+=1
        elif gold!=predicted and gold==0:
            fp+=1
    if tp+fp>0:
        prec = tp/(tp+fp)
    else:
        prec = 0
    if tp+fn>0:
        rec = tp/(tp+fn)
    else:
        rec = 0
    if prec+rec>0:
        f1 = 2*prec*rec/(prec+rec)
    else:
        f1 = 0
    return {"f1": f1}

# training the model

def training():
    config = AdapterConfig.load("pfeiffer")
    model.add_adapter(task, config=config)
    model.add_classification_head(task, num_labels=len(label2id), id2label=id2label, use_pooler=True)
    model.set_active_adapters(task)
    model.train_adapter(task)

    train_dataset = datasets.Dataset.from_csv(data_folder+"/"+low_resource_annotation_prefix+"train.csv")
    train_dataset = train_dataset.map(encode_data, batched=True, batch_size=batch_size)
    train_dataset = train_dataset.rename_column("tokens","text").rename_column("tags","labels")

    dev_dataset = datasets.Dataset.from_csv(data_folder+"/"+low_resource_annotation_prefix+"dev.csv")
    dev_dataset = dev_dataset.map(encode_data, batched=True, batch_size=batch_size)
    dev_dataset = dev_dataset.rename_column("tokens","text").rename_column("tags","labels")

    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    dev_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

    model.to(device)


    training_args = TrainingArguments(
        learning_rate=1e-3,
        num_train_epochs=20,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        logging_steps=100,
        output_dir="training_output",
        overwrite_output_dir=True,
        remove_unused_columns=False,
    )


    trainer = AdapterTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        compute_metrics=compute_accuracy,
    )

    trainer.train()
    print(trainer.evaluate())
    if anno_type=="low_resource_turn_and_speaker":
        dir = "adapters/low_res"+task+"_"+low_resource_annotation_prefix.replace(".","-")
    else:
        dir = "adapters/"+task+"_"+anno_type
    dir = Path(dir)
    if not dir.exists():
        dir.mkdir(parents=True)
    model.save_adapter(dir, task)

# test evaluation
def evaluation():
    intexts = []
    gold_labels = []
    test_dataset = datasets.Dataset.from_csv(data_folder+"/"+"test.csv")
    test_dataset = test_dataset.map(encode_data, batched=True, batch_size=1)

    for i in range(len(test_dataset)):
        if anno_type=="iso_simplified" or anno_type=="iso":
            intexts.append(test_dataset["speakers"][i]+" [SEP] "+test_dataset["isoda"][i]+" [SEP] "+test_dataset["tokens"][i])
        elif anno_type=="summary":
            if test_dataset["summary"][i] is not None:
                truncated_summary = " ".join(test_dataset["summary"][i].split()[-250:])
            else:
                truncated_summary = "Start"
            intexts.append(truncated_summary+" [SEP] "+test_dataset["speakers"][i]+" [SEP] "+test_dataset["tokens"][i])
        if anno_type=="without_context_and_without_speaker":
            intexts.append(test_dataset["tokens"][i])
        elif anno_type=="without_context_with_current_speaker" or anno_type=="low_resource_turn_and_speaker":
            intexts.append(test_dataset["speakers"][i]+" [SEP] "+test_dataset["tokens"][i])
        elif anno_type=="with_context_with_current_and_previous_speaker":
            intexts.append(test_dataset["previous_speakers"][i]+" [SEP] "+test_dataset["previous"][i]+" [SEP] "+test_dataset["speakers"][i]+" [SEP] "+test_dataset["tokens"][i])
        elif anno_type=="with_context":
            intexts.append(test_dataset["previous"][i] + " [SEP] " + test_dataset["tokens"][i])
        gold_labels.append(test_dataset["tags"][i])

    if anno_type=="low_resource_turn_and_speaker":
        model.load_adapter("adapters/low_res"+task+"_"+low_resource_annotation_prefix.replace(".","-"))
    else:
        model.load_adapter("adapters/"+task+"_"+anno_type+"/")

    model.active_adapters = task
    model.active_head = task

    dact_classifier = pipeline(model=model, tokenizer=tokenizer, task="text-classification", device=0 if device=="cuda" else -1)
    # if anno_type=="iso":
    #     all_labels = ["Answer", "Disconfirm", "Inform", "Request", "Offer", "Confirm", "Auto-positive", "TurnAccept", "Question", "TurnAssign", "PropositionalQuestion", "Agreement", "Promise", "TurnTake", "AddressRequest", "AcceptOffer", "AcceptRequest", "Pausing", "CheckQuestion", "DeclineOffer", "Auto-negative", "SetQuestion", "ChoiceQuestion", "Instruct", "Allo-positive", "Other"]
    # else:
    #     all_labels = ["Absage", "Einsatzbefehl", "Information_geben", "Information_nachfragen", "Kontakt_Anfrage", "Kontakt_Bestaetigung", "Sonstiges", "Zusage"]
    all_labels = label2id.keys()

    scores = dict()
    for label in all_labels:
        scores[label] = {"tp":0, "fp":0, "fn":0}
    match = 0
    for i, intext in enumerate(intexts):
        predicted_label = ""
        prediction = dact_classifier(intext)
        if len(prediction)>0:
            predicted_label = prediction[0]["label"]
        gold_label = id2label[gold_labels[i]]
        if predicted_label==gold_label:
            match+=1
            scores[predicted_label]["tp"]+=1
        else:
            #print(prediction, intext, ">>>", predicted_label, gold_label)
            scores[predicted_label]["fp"]+=1
            scores[gold_label]["fn"]+=1
    print("Accuracy:", round(match/len(intexts),3), "matched:", match, "total:", len(intexts))
    print("F1 scores:")
    f1scores = 0
    # compute f1 scores (per label)
    for label in all_labels:
        tp = scores[label]["tp"]
        fp = scores[label]["fp"]
        fn = scores[label]["fn"]
        if tp+fp>0:
            prec = tp/(tp+fp)
        else:
            prec = 0
        if tp+fn>0:
            rec = tp/(tp+fn)
        else:
            rec = 0
        if prec+rec>0:
            f1score = 2*prec*rec/(prec+rec)
        else:
            f1score = 0
        f1scores+=f1score
        print(label, "F1:", round(f1score,3))
    # compute macro f1 score (avg)
    print("Macro F1:", round(f1scores/len(all_labels),3))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-t":
        training()
    else:
        evaluation()
