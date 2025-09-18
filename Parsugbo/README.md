# ParSugbo

## Setup

### Prerequisites

- Python 3.13 or higher
- PDM (Python Development Master)

### Installing PDM

To install PDM, you can use the following command:

```sh
pip install pdm
```

### Setting Up the Project

1. Clone the repository:

   ```sh
   git clone https://github.com/NoodleSushi/ParSugbo.git
   cd ParSugbo
   ```

1. Install the dependencies using PDM:

   ```sh
   pdm install
   ```

### Running the Project

To run the project, use the following command:

```sh
pdm run python -m parsugbo --input "ang bata naligo sa sapa"
```

```txt
ang bata naligo sa sapa
No errors
'Sentence Part'
    |-->'Sentence'
        |-->'Predicate Phrase'
            |-->'Predicate'
                |-->'Noun Phrase Part'
                    |-->'Noun Phrase'
                        |-->'Singular Noun Phrase'
                            |-->'DET->ang'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Singular Noun'
                                |-->'Empty'
                                |-->'Empty'
                                |-->'NOUN->bata'
                                |-->'Empty'
                            |-->'Empty'
                        |-->'Empty'
                        |-->'Empty'
                        |-->'Empty'
            |-->'Empty'
            |-->'Verb Phrase'
                |-->'Complex Verb'
                    |-->'PAST_PREFIX, PRESENT_PREFIX->na'
                    |-->'VERB->ligo'
                    |-->'Empty'
                |-->'Noun Phrase Part'
                    |-->'Noun Phrase'
                        |-->'Singular Noun Phrase'
                            |-->'DET->sa'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Empty'
                            |-->'Singular Noun'
                                |-->'Empty'
                                |-->'Empty'
                                |-->'Empty'
                            |-->'Empty'
                        |-->'Empty'
                        |-->'Empty'
                        |-->'Empty'
            |-->'Empty'
        |-->'Noun Phrase Part'
            |-->'Empty'
```
