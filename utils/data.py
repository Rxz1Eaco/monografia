import pandas as pd
import numpy as np
import streamlit as st


def base_dados():
    df = pd.read_csv("data/despesas_MA_2025_pagamentos.csv", sep=",")

    return df


base_dados()
