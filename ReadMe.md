# Dialogue intent classification and slot recognition for DRZ

This is a modified copy of the `slot-tagging` subdirectory of the [emergency_response_dialogue](https://github.com/tanikina/emergency_response_dialogue) github repository. The functionality to recognise the dialogue act first and only call slot tagging for certain dialogue acts has been added, which is basically the same as in the `dialogue_act_classification` directory of the above repository.

Original code from [tanikina](https://github.com/tanikina) , server functionality from [jsteffen](https://github.com/jsteffen)

The Bert base model is only loaded once and the adapters are dynamically switched depending on the task. To download the base model to your machine, execute the following in the project root directory:

```
git clone https://huggingface.co/bert-base-german-cased
```

This is also necessary when the docker image is used with `run_docker.sh`

# Start server locally

First make sure you have proper `.venv` (we use `uv` for package management)

    uv sync

Now start the server

    uv run ./adapters_bio_tags_server.py [-h <host>] [-p <port>]

or

    . .venv/bin/activate
    ./adapters_bio_tags_server.py [-h <host>] [-p <port>]

# Test server functionality

You can check what the server returns using the following command line
```
curl -G --data-urlencode 'text=Wassertrupp mit dem Rollschlauch zur Brandbekämpfung vor' --data-urlencode 'prev_text=Truppführer hört' 'http://localhost:5050/annotate'
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
