# Dialogue intent classification and slot recognition for DRZ

This is a modified copy of the `slot-tagging` subdirectory of the [emergency_response_dialogue](https://github.com/tanikina/emergency_response_dialogue) github repository. The functionality to recognise the dialogue act first and only call slot tagging for certain dialogue acts has been added, which is basically the same as in the `dialogue_act_classification` directory of the above repository.

Original code from [tanikina](https://github.com/tanikina) , server functionality from [jsteffen](https://github.com/jsteffen)

The Bert base model is only loaded once and the adapters are dynamically switched depending on the task. To download the base model to your machine, execute the following in the project root directory:

```
git clone https://huggingface.co/bert-base-german-cased
```

This is also necessary when the docker image is used with `run_docker.sh`

# Start server

```
./adapters_bio_tags_server.py [-h <host>] [-p <port>]
```

# Test server functionality

You can check what the server returns using the following command line
```
curl -G --data-urlencode 'text=Wassertrupp mit dem Rollschlauch zur Brandbekämpfung vor' 'http://localhost:5050/annotate'
```

# Train slot tagging modules for DRZ (Einsatzbefehl)
This trains and evaluates a set of adapters for important information bits in DRZ radio communication. Training and evaluation can also be done with the docker image, since it contains all necessary functionality.

After setting up the appropriate venv or conda environment with the requirements specified in `requirements.txt`, the adapters can be trained and evaluated like this:

```
python adapters_bio_tags.py -t
python adapters_bio_tags.py
```

This will create adapters based on the `neg_samples_csv` data set under the `balanced` adapters subdirectory.

The same can be done for the dialogue act recognition: (current default mode: with_context)

```
./adapters_classifier.py -t
./adapters_classifier.py
```

Models for the dialogue act classification must be moved to the appropriate folder to be usable by the server code.

# Identify slots using an LLM

Install **vLLM** to run inference with an LLM. Note: adapter tuning is performed without vLLM, however, vLLM is used to do inference with the tuned adapter.

1. Inference with an LLM. 

The task is defined as follows. Given an utterance and a type of slot we are interested in *(Auftrag, Einheit, Ziel, Weg, Mittel)*, the model is to generate the same utterance where the start and the end of the desired slot are marked with the ** symbols. If the given slot is absent, the model is to generate the utterance without any markers. The prompt for the task contains an instruction, slot definitions and 5 demonstrations, based on semantic similarity with the target utterance. The demonstrations are picked out from the training data. To do the inference, on DFKI cluster execute:

```
sbatch ./srun_scripts/slot_identification_llm.srun
```

2. Fine-tuning a LoRA adapter on top of an LLM. 

The task is defined in the same way as before. The prompt used during training is similar, but the demonstrations are removed. The training is done using the training partition of the data. To tune an adapter, on DFKI cluster execute:

```
sbatch ./srun_scripts/slot_identification_llm_adapter.srun
```

To evaluate the tuned LoRA adapter, execute the following script on the DFKI cluster:

```
sbatch ./srun_scripts/slot_identification_llm_adapter_eval.srun
```

Note: Modify the virtual environment names/locations in the SRUN scripts, if needed.