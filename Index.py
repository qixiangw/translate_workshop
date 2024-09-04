import streamlit as st

st.set_page_config(
    page_title="Workshop Index",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
## introduction
info here
## getting started

1. To install the workshop, follow these steps:
```bash
# install miniconda
    ## mac
    brew install miniconda
    ## other systems
    [miniconda installer](https://docs.conda.io/en/latest/miniconda.html)
# Create a new conda environment with Python 3.10
conda create -n py310 python=3.10

# Activate the conda environment
conda activate py310

# Clone the repository to your local machine
git clone  ...

# Navigate to the project directory
cd smart-marketing-llm-workshop

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

2. After installing, you can launch the application simply by running:

```bash
streamlit run app.py
```
## workshop 
1. [Tanslate Text](/translate)
2. [marketing note](/mkt_content)
3. [Document Translate](/agent)
            """)


### word and ppt translate 
##########################################
#########to do 写一个目录即可###############
##########################################