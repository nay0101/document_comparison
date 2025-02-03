# Multilingual Document Comparison

## Set Up

### Create Virtual Environment

```
python -m venv venv
```

### Activate Virtual Environment

```
vevn/Scripts/activate
```

### Installation

```
pip install -r requirements.txt
```

### Prepare .env

```
cp .env.example .env
```

### Run Document Compare Agent

```
streamlit run app.py --server.port 8501
```

### Run Guideline Compare Agent

```
streamlit run app.py --server.port 8502
```
