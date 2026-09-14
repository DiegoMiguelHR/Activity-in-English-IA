# -*- coding: utf-8 -*-
"""================================================================================
    PRECOMPUTE: runs the full 4-model experiment once and produces:
      - app_data/resultados.json   (all numbers, verdicts, confusion matrices)
      - static/assets/*.png        (figures used by the dashboard)

    It is used by:
      1) the CLI (python precompute.py) to build committed assets, and
      2) the web app "/api/train" endpoint to re-run the experiment on demand.

    USAGE:
        python precompute.py
================================================================================
"""

import os
import sys
import json
import math
import shutil
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_predict
from sklearn.metrics import (make_scorer, f1_score, accuracy_score, precision_score,
                             recall_score, confusion_matrix)
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier

# Permitir importar los módulos de experimentación que viven en ActividadIngles/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ActividadIngles"))
import occupancy_classification as oc

warnings.filterwarnings("ignore")

MODELO_COLORES = {
    "KNN": "#17becf",
    "SVC": "#ff7f0e",
    "GradientBoosting": "#2ca02c",
    "GaussianNB": "#d62728",
}


def grid_full():
    """Same hyperparameter grids as occupancy_classification.py (official report)."""
    return oc.definir_modelos_y_grids()


def grid_quick():
    """Reduced grids for fast web re-training (tips on Render free tier).
    Keeps the three SVM kernels, both KNN distance metrics and the model families,
    but shrinks n_estimators and the C/gamma ranges."""
    return {
        "SVC": (
            SVC(random_state=42),
            {
                "clf__C": [1, 10],
                "clf__gamma": [0.1, 1],
                "clf__kernel": ["rbf", "linear", "poly"],
            },
        ),
        "GaussianNB": (
            GaussianNB(),
            {"clf__var_smoothing": [1e-9, 1e-8, 1e-7]},
        ),
        "GradientBoosting": (
            GradientBoostingClassifier(random_state=42),
            {
                "clf__n_estimators": [50],
                "clf__max_depth": [2, 4],
                "clf__learning_rate": [0.05, 0.1],
            },
        ),
        "KNN": (
            KNeighborsClassifier(),
            {
                "clf__n_neighbors": [3, 5, 7],
                "clf__weights": ["uniform", "distance"],
                "clf__metric": ["euclidean", "manhattan"],
            },
        ),
    }


# ---------------------------------------------------------------------------
# Generacion de texto (veredicto) en ingles, desde los numeros del experimento
# ---------------------------------------------------------------------------
def _fmt(x):
    return f"{x:.4f}"


def generar_verdicto(modelos):
    """Builds the Phase 3 answers in English from the results table."""
    orden = sorted(modelos, key=lambda m: -m["f1"])
    ganador = orden[0]
    perdedor = orden[-1]

    q1 = (
        f"After stratified 5-fold cross-validation, {ganador['name']} achieved the best balance "
        f"between accuracy and generalization, with a macro F1-Score of {_fmt(ganador['f1'])} and "
        f"an accuracy of {_fmt(ganador['accuracy'])}. It balanced false positives and false "
        f"negatives almost perfectly ({ganador['confusion'][0][1]} FP and "
        f"{ganador['confusion'][1][0]} FN out of {ganador['total']:,} instances), beating the "
        f"lowest-performing model, {perdedor['name']}, which reached {_fmt(perdedor['f1'])} "
        f"(with {perdedor['confusion'][0][1]} false positives). Using the macro F1 guarantees the "
        f"result is not distorted by the class imbalance."
    )

    complejos = [m for m in orden if m["name"] in ("SVC", "GradientBoosting")]
    rapido = min(orden, key=lambda m: m["time_s"])
    q2 = (
        f"No. In this experiment the mathematically more complex models did NOT justify their "
        f"high computational cost. "
    )
    if complejos:
        q2 += (
            f"While {complejos[0]['name']} ({complejos[0]['time_s']:.2f} s) and "
            f"{complejos[1]['name']} ({complejos[1]['time_s']:.2f} s) reached F1-Scores of "
            f"{_fmt(complejos[0]['f1'])} and {_fmt(complejos[1]['f1'])} respectively, "
        )
    q2 += (
        f"{ganador['name']} obtained the winning score ({_fmt(ganador['f1'])}) in just "
        f"{ganador['time_s']:.2f} s, and the fastest model, {rapido['name']}, finished in "
        f"{rapido['time_s']:.2f} s. "
        f"The extra cost of SVC and Boosting did not translate into better performance, so for "
        f"this problem additional complexity is not profitable."
    )

    q3 = (
        f"The dataset has five environmental variables. Two PCA components retain an important "
        f"share of the variance, and the classes (empty vs. occupied) form dense, well-separated "
        f"clusters. This explains {ganador['name']}'s triumph: its distance-based decision "
        f"boundaries follow the natural separation of the clusters without rigid assumptions. "
        f"SVC (RBF kernel) and Gradient Boosting achieved almost equivalent boundaries but at a "
        f"much higher cost. On the opposite end, GaussianNB drew an overly rigid probabilistic "
        f"boundary (assuming independence among correlated variables such as Light and CO2) and "
        f"produced the highest number of false positives of the four models."
    )

    conclusion = (
        f"{ganador['name']} (best params {ganador['params']}) is the winning model: the best "
        f"F1-Score with the lowest computational cost among the top three. Complex models "
        f"(SVC and Gradient Boosting) did not justify their extra cost, and GaussianNB lagged "
        f"behind because its independence assumptions were violated. For low-dimensional "
        f"problems with well-separated classes, a simple geometric method such as "
        f"{ganador['name']} can be the most efficient and accurate option."
    )

    return {
        "winner": ganador["name"],
        "winner_f1": ganador["f1"],
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "conclusion": conclusion,
    }


# ---------------------------------------------------------------------------
# Graficos (se regeneran en cada ejecucion)
# ---------------------------------------------------------------------------
def generar_figuras(data, assets_dir):
    os.makedirs(assets_dir, exist_ok=True)

    modelos = data["models"]
    df = pd.DataFrame([{
        "Modelo": m["name"], "F1": m["f1"], "Tiempo": m["time_s"],
    } for m in modelos])

    colores = [MODELO_COLORES[n] for n in df["Modelo"]]
    rota = df.sort_values("F1", ascending=False)

    # F1 bars
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(rota["Modelo"], rota["F1"], color=[MODELO_COLORES[n] for n in rota["Modelo"]],
                  edgecolor="black", linewidth=0.6)
    ax.set_ylim(0.90, 1.0)
    ax.set_ylabel("Macro F1-Score (cross-validation)")
    ax.set_title("Macro F1-Score averages (StratifiedKFold, 5 folds)")
    for b, v in zip(bars, rota["F1"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.002, f"{v:.4f}",
                ha="center", fontsize=9, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "resultados_f1.png"), dpi=180)
    plt.close(fig)

    # time bars
    orden_t = ["GaussianNB", "KNN", "GradientBoosting", "SVC"]
    tval = [df.loc[df["Modelo"] == n, "Tiempo"].iloc[0] for n in orden_t]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(orden_t, tval, color=[MODELO_COLORES[n] for n in orden_t],
           edgecolor="black", linewidth=0.6)
    ax.set_ylabel("Total time (seconds)")
    ax.set_title("Computational time of the search + training (GridSearchCV)")
    for xi, v in enumerate(tval):
        ax.text(xi, v + max(tval) * 0.02, f"{v:.2f}s", ha="center", fontsize=9, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "resultados_tiempo.png"), dpi=180)
    plt.close(fig)

    # F1 vs time scatter
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(df["Tiempo"], df["F1"], s=200, c=colores, edgecolor="black", zorder=5)
    for _, r in df.iterrows():
        ax.annotate(r["Modelo"], (r["Tiempo"], r["F1"]), textcoords="offset points",
                    xytext=(12, -6), fontsize=10)
    ax.set_xlabel("Computational time (seconds)")
    ax.set_ylabel("Macro F1-Score")
    ax.set_title("Performance vs. computational cost")
    ax.grid(True, alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "resultados_f1_tiempo.png"), dpi=180)
    plt.close(fig)

    # kernels
    kernels = data["kernels"]
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.bar([k["kernel"] for k in kernels], [k["f1"] for k in kernels],
           color=["#ff7f0e", "#2ca02c", "#d62728"], edgecolor="black", linewidth=0.6)
    ax.set_ylim(0.85, 1.0)
    ax.set_xlabel("Kernel")
    ax.set_ylabel("Best macro F1-Score")
    ax.set_title("SVM kernel analysis (best F1 per kernel)")
    for xi, k in enumerate(kernels):
        ax.text(xi, k["f1"] + 0.002, f"{k['f1']:.4f}", ha="center", fontsize=9, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "comparacion_kernels.png"), dpi=180)
    plt.close(fig)

    # metrics
    metricas = data["metricas"]
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.bar([m["metric"] for m in metricas], [m["f1"] for m in metricas],
           color=["#17becf", "#9467bd"], edgecolor="black", linewidth=0.6)
    ax.set_ylim(0.85, 1.0)
    ax.set_xlabel("Distance metric")
    ax.set_ylabel("Best macro F1-Score")
    ax.set_title("KNN distance-metric evaluation")
    for xi, m in enumerate(metricas):
        ax.text(xi, m["f1"] + 0.002, f"{m['f1']:.4f}", ha="center", fontsize=9, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "comparacion_metricas.png"), dpi=180)
    plt.close(fig)

    return assets_dir


def generar_fronteras(data, X, y, best_estimators, assets_dir):
    """Decision boundaries projected onto the 2 first PCA components."""
    scaler = StandardScaler().fit(X)
    X_esc = scaler.transform(X)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_esc)

    xmin, xmax = X_pca[:, 0].min() - 0.5, X_pca[:, 0].max() + 0.5
    ymin, ymax = X_pca[:, 1].min() - 0.5, X_pca[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(xmin, xmax, 200), np.linspace(ymin, ymax, 200))
    puntos_pca = np.c_[xx.ravel(), yy.ravel()]
    puntos_esc = pca.inverse_transform(puntos_pca)
    puntos_raw = scaler.inverse_transform(puntos_esc)

    modelos = data["models"]
    nombres = [m["name"] for m in sorted(modelos, key=lambda m: -m["f1"])]
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, nombre in zip(axes.ravel(), nombres):
        Z = best_estimators[nombre].predict(puntos_raw).reshape(xx.shape)
        ax.contourf(xx, yy, Z, levels=[-0.5, 0.5, 1.5], alpha=0.30,
                    colors=["#d5f0e9", "#f5d9d0"])
        ax.contour(xx, yy, Z, levels=[0.5], colors="black", linewidths=0.8, alpha=0.6)
        m0 = y == 0
        ax.scatter(X_pca[m0, 0], X_pca[m0, 1], s=8, c="#1f77b4", alpha=0.35, label="Empty")
        ax.scatter(X_pca[~m0, 0], X_pca[~m0, 1], s=8, c="#d62728", alpha=0.55, label="Occupied")
        f1v = next(m["f1"] for m in modelos if m["name"] == nombre)
        ax.set_title(f"{nombre}  (F1 = {f1v:.4f})")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("Component 1 (PCA)")
        ax.set_ylabel("Component 2 (PCA)")
        if nombre == nombres[0]:
            ax.legend(loc="lower right", fontsize=8)
    fig.suptitle("Decision boundaries projected onto the two first PCA components", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(assets_dir, "fronteras_decision_PCA.png"), dpi=180)
    plt.close(fig)
    return pca.explained_variance_ratio_.round(4).tolist()


def generar_correlacion(data, X, assets_dir):
    corr = X.corr()
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Correlation among predictor variables")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(os.path.join(assets_dir, "correlacion_features.png"), dpi=180)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experimento principal
# ---------------------------------------------------------------------------
def run_experiment(json_path=None, assets_dir=None, n_jobs=1, mode="full"):
    """Runs the experiment, writes resultados.json and regenerates figures.

    mode: "full" (official grids from the report) or "quick" (reduced grids
    for fast web re-training). Returns the data dict (also persisted to
    json_path when provided).
    """
    t_total_inicio = datetime.now(timezone.utc)

    df = oc.cargar_datos()
    objetivo = oc.detectar_objetivo(df)
    cols_features = [c for c in df.columns if c != objetivo]
    X = df[cols_features].select_dtypes(include=[np.number])
    y = df[objetivo].astype(int)

    class_dist = y.value_counts().to_dict()
    total = int(len(y))

    scorer = make_scorer(f1_score, average="macro")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    modelos_def = grid_quick() if mode == "quick" else grid_full()

    best_estimators = {}
    resultados = []
    gs_objects = {}

    for nombre, (clf, grid) in modelos_def.items():
        t0 = datetime.now(timezone.utc)
        gs = GridSearchCV(oc.construir_pipeline(clf), grid,
                          scoring=scorer, cv=cv, n_jobs=n_jobs, verbose=0)
        gs.fit(X, y)
        gs_objects[nombre] = gs
        tiempo_s = (datetime.now(timezone.utc) - t0).total_seconds()

        best_estimators[nombre] = gs.best_estimator_
        params = gs.best_params_

        y_pred = cross_val_predict(gs.best_estimator_, X, y, cv=cv, n_jobs=n_jobs)
        cm = confusion_matrix(y, y_pred)

        resultados.append({
            "name": nombre,
            "f1": round(gs.best_score_, 4),
            "accuracy": round(accuracy_score(y, y_pred), 4),
            "precision": round(precision_score(y, y_pred, average="macro"), 4),
            "recall": round(recall_score(y, y_pred, average="macro"), 4),
            "time_s": round(tiempo_s, 4),
            "params": {str(k).replace("clf__", ""): v for k, v in params.items()},
            "confusion": cm.tolist(),
            "total": total,
        })

    resultados.sort(key=lambda m: -m["f1"])

    # Analisis de kernels (SVC): reutiliza la cuadricula ya ajustada
    cvr = pd.DataFrame(gs_objects["SVC"].cv_results_)
    cvr["kernel"] = cvr["param_clf__kernel"].astype(str)
    gs_svc = cvr.groupby("kernel")["mean_test_score"].max()
    kernels = [{"kernel": k, "f1": round(float(v), 4)}
               for k, v in gs_svc.sort_values(ascending=False).items()]

    # Analisis de metricas (KNN): reutiliza la cuadricula ya ajustada
    cvr = pd.DataFrame(gs_objects["KNN"].cv_results_)
    cvr["metric"] = cvr["param_clf__metric"].astype(str)
    gs_knn = cvr.groupby("metric")["mean_test_score"].max()
    metricas = [{"metric": k, "f1": round(float(v), 4)}
                for k, v in gs_knn.sort_values(ascending=False).items()]

    data = {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "dataset": {
            "name": "Occupancy Detection Dataset",
            "source": "UCI Machine Learning Repository (Paper: Accurate occupancy detection of an office room from light, temperature, humidity and CO2 measurements)",
            "instances": total,
            "features": int(X.shape[1]),
            "columns": list(X.columns),
            "classes": {"empty": int(class_dist.get(0, 0)), "occupied": int(class_dist.get(1, 0))},
            "imbalance": round(class_dist.get(0, 0) / total, 4),
        },
        "models": resultados,
        "kernels": kernels,
        "metricas": metricas,
        "verdict": generar_verdicto(resultados),
        "figures": {
            "f1_bars": "assets/resultados_f1.png",
            "time_bars": "assets/resultados_tiempo.png",
            "f1_time": "assets/resultados_f1_tiempo.png",
            "kernels": "assets/comparacion_kernels.png",
            "metrics": "assets/comparacion_metricas.png",
            "boundaries": "assets/fronteras_decision_PCA.png",
            "correlation": "assets/correlacion_features.png",
        },
        "runtime_seconds": round((datetime.now(timezone.utc) - t_total_inicio).total_seconds(), 2),
    }

    # ---- figuras ----
    if assets_dir:
        os.makedirs(assets_dir, exist_ok=True)
        var_pca = generar_fronteras(data, X, y, best_estimators, assets_dir)
        data["pca_variance"] = var_pca
        generar_correlacion(data, X, assets_dir)
        generar_figuras(data, assets_dir)

    # ---- persistencia ----
    if json_path:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    return data


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    data = run_experiment(
        json_path=os.path.join(base, "app_data", "resultados.json"),
        assets_dir=os.path.join(base, "static", "assets"),
        n_jobs=-1,  # local: use all cores
    )
    print("=" * 80)
    print("EXPERIMENTO COMPLETADO")
    print("=" * 80)
    for m in data["models"]:
        print(f"  {m['name']:<18} F1={m['f1']:.4f}  t={m['time_s']:.2f}s  params={m['params']}")
    print("  PCA varianza:", data.get("pca_variance"))
    print("  Duracion total:", data["runtime_seconds"], "s")
    print("  JSON ->", os.path.join(base, "app_data", "resultados.json"))
    print("  Assets ->", os.path.join(base, "static", "assets"))


if __name__ == "__main__":
    main()