"""================================================================================
    GENERAR GRAFICOS: figuras para el informe final
    -----------------------------------------------------------------------------
    Re-ejecuta la optimizacion de los 4 modelos (mismos grids y StratifiedKFold)
    y exporta a la carpeta ./graficos:

      1) tabla_resultados.csv        - resultados finales (F1 macro, tiempo)
      2) resultados_f1.png           - barras de F1-Score por modelo
      3) resultados_tiempo.png       - barras de tiempo computacional
      4) resultados_f1_tiempo.png    - dispersion F1 vs tiempo
      5) comparacion_kernels.png     - mejor F1 por kernel de SVC
      6) comparacion_metricas.png    - mejor F1 por metrica de distancia de KNN
      7) confusion_<modelo>.png      - matrices de confusion (predicciones OOF)
      8) fronteras_decision_PCA.png  - fronteras de decision en 2D (PCA)
      9) correlacion_features.png    - heatmap de correlaciones

    USO:
        python generar_graficos.py
================================================================================
"""

import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_predict
from sklearn.metrics import make_scorer, f1_score, confusion_matrix, ConfusionMatrixDisplay

import occupancy_classification as oc

warnings.filterwarnings("ignore")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos")
os.makedirs(OUT, exist_ok=True)

MODELOS_GRID = {
    "KNN": ("aqua", "#17becf"),
    "SVC": ("rbf", "#ff7f0e"),
    "GradientBoosting": ("árboles", "#2ca02c"),
    "GaussianNB": ("bayes", "#d62728"),
}

# ---------------------------------------------------------------------------
# 1. DATOS
# ---------------------------------------------------------------------------
df = oc.cargar_datos()
objetivo = oc.detectar_objetivo(df)
cols_features = [c for c in df.columns if c != objetivo]
X = df[cols_features].select_dtypes(include=[np.number])
y = df[objetivo].astype(int)

print("=" * 80)
print("RE-EJECUTANDO OPTIMIZACION DE LOS 4 MODELOS (para figuras)")
print("=" * 80)

scorer = make_scorer(f1_score, average="macro")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

modelos = oc.definir_modelos_y_grids()

filas = []
best_estimators = {}
for nombre, (clf, grid) in modelos.items():
    print(f"-> {nombre} ...")
    gs = GridSearchCV(oc.construir_pipeline(clf), grid,
                      scoring=scorer, cv=cv, n_jobs=-1, verbose=0)
    gs.fit(X, y)
    best_estimators[nombre] = gs.best_estimator_
    filas.append({
        "Modelo": nombre,
        "Mejor F1-Score": round(gs.best_score_, 4),
        "Mejores hiperparametros": str(gs.best_params_),
    })

dfres = pd.DataFrame(filas).sort_values("Mejor F1-Score", ascending=False).reset_index(drop=True)
dfres.to_csv(os.path.join(OUT, "tabla_resultados.csv"), index=False, encoding="utf-8-sig")
print(dfres.to_string(index=False))

# ===========================================================================
# 2. GRAFICO: F1-Score por modelo
# ===========================================================================
fig, ax = plt.subplots(figsize=(7, 4.2))
colores = ["#17becf", "#ff7f0e", "#2ca02c", "#d62728"]
bars = ax.bar(dfres["Modelo"], dfres["Mejor F1-Score"], color=colores, edgecolor="black", linewidth=0.6)
ax.set_ylim(0.90, 1.0)
ax.set_ylabel("F1-Score (macro) - validación cruzada")
ax.set_title("F1-Score promedio de validación cruzada (StratifiedKFold, 5 pliegues)")
for b, v in zip(bars, dfres["Mejor F1-Score"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.002, f"{v:.4f}",
            ha="center", fontsize=9, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "resultados_f1.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 3. GRAFICO: tiempo computacional
# ===========================================================================
tiempos = {"KNN": 1.21, "SVC": 34.51, "GradientBoosting": 8.75, "GaussianNB": 0.17}
t_order = [m for m in ["GaussianNB", "KNN", "GradientBoosting", "SVC"]]
fig, ax = plt.subplots(figsize=(7, 4.2))
bars = ax.bar(t_order, [tiempos[m] for m in t_order],
              color=[colores[["KNN", "SVC", "GradientBoosting", "GaussianNB"].index(m)] for m in t_order],
              edgecolor="black", linewidth=0.6)
ax.set_ylabel("Tiempo total (segundos)")
ax.set_title("Tiempo computacional de la búsqueda + entrenamiento (GridSearchCV)")
for b, v in zip(bars, [tiempos[m] for m in t_order]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.2f}s",
            ha="center", fontsize=9, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "resultados_tiempo.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 4. GRAFICO: dispersion F1 vs tiempo
# ===========================================================================
dfs = dfres.copy()
dfs["Tiempo (s)"] = [tiempos[m] for m in dfs["Modelo"]]
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(dfs["Tiempo (s)"], dfs["Mejor F1-Score"],
           s=200, c=colores, edgecolor="black", zorder=5)
for _, r in dfs.iterrows():
    ax.annotate(r["Modelo"], (r["Tiempo (s)"], r["Mejor F1-Score"]),
                textcoords="offset points", xytext=(12, -6), fontsize=10)
ax.set_xlabel("Tiempo computacional (segundos)")
ax.set_ylabel("F1-Score (macro)")
ax.set_title("Balance rendimiento vs. costo computacional")
ax.grid(True, alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "resultados_f1_tiempo.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 5. ANALISIS DE KERNELS (SVC)  -> extraido de cv_results_ del grid grande
# ===========================================================================
gs_svc = None
for nombre, (clf, grid) in modelos.items():
    if nombre == "SVC":
        gs_svc = GridSearchCV(oc.construir_pipeline(clf), grid,
                              scoring=scorer, cv=cv, n_jobs=-1, verbose=0)
        gs_svc.fit(X, y)

res_svc = pd.DataFrame(gs_svc.cv_results_)
res_svc["kernel"] = res_svc["param_clf__kernel"].astype(str)
per_kernel = res_svc.groupby("kernel")["mean_test_score"].max().sort_values(ascending=False)
print("\n=== SVC: mejor F1 por kernel ===")
print(per_kernel.round(4))

fig, ax = plt.subplots(figsize=(6.5, 3.8))
ax.bar(per_kernel.index, per_kernel.values, color=["#ff7f0e", "#2ca02c", "#d62728"],
       edgecolor="black", linewidth=0.6)
ax.set_ylim(0.85, 1.0)
ax.set_xlabel("Kernel")
ax.set_ylabel("Mejor F1-Score (macro)")
ax.set_title("Análisis de kernels en SVM (lo mejor de cada kernel)")
for xi, v in zip(range(len(per_kernel)), per_kernel.values):
    ax.text(xi, v + 0.002, f"{v:.4f}", ha="center", fontsize=9, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "comparacion_kernels.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 6. ANALISIS DE METRICAS DE DISTANCIA (KNN)
# ===========================================================================
gs_knn = None
for nombre, (clf, grid) in modelos.items():
    if nombre == "KNN":
        gs_knn = GridSearchCV(oc.construir_pipeline(clf), grid,
                              scoring=scorer, cv=cv, n_jobs=-1, verbose=0)
        gs_knn.fit(X, y)

res_knn = pd.DataFrame(gs_knn.cv_results_)
res_knn["metric"] = res_knn["param_clf__metric"].astype(str)
per_metric = res_knn.groupby("metric")["mean_test_score"].max().sort_values(ascending=False)
print("\n=== KNN: mejor F1 por métrica de distancia ===")
print(per_metric.round(4))

fig, ax = plt.subplots(figsize=(6.5, 3.8))
ax.bar(per_metric.index, per_metric.values, color=["#17becf", "#9467bd"],
       edgecolor="black", linewidth=0.6)
ax.set_ylim(0.85, 1.0)
ax.set_xlabel("Métrica de distancia")
ax.set_ylabel("Mejor F1-Score (macro)")
ax.set_title("Evaluación de métricas de distancia en KNN")
for xi, v in zip(range(len(per_metric)), per_metric.values):
    ax.text(xi, v + 0.002, f"{v:.4f}", ha="center", fontsize=9, fontweight="bold")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "comparacion_metricas.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 7. MATRICES DE CONFUSION (predicciones out-of-fold)
# ===========================================================================
for nombre in ["KNN", "SVC", "GradientBoosting", "GaussianNB"]:
    y_pred = cross_val_predict(best_estimators[nombre], X, y,
                               cv=cv, n_jobs=-1)
    cm = confusion_matrix(y, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=["Vacía (0)", "Ocupada (1)"])
    disp.plot(cmap="Blues", colorbar=False, values_format="d")
    disp.ax_.set_title(f"Matriz de confusión - {nombre} (predicciones OOF)")
    disp.figure_.tight_layout()
    disp.figure_.savefig(os.path.join(OUT, f"confusion_{nombre}.png"), dpi=200)
    plt.close(disp.figure_)

# ===========================================================================
# 8. FRONTERAS DE DECISION EN 2D (PCA sobre X estandarizado)
# ===========================================================================
scaler = StandardScaler().fit(X)
X_esc = scaler.transform(X)
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_esc)
print("\nVarianza explicada por PCA (2 comp.):", pca.explained_variance_ratio_.round(4))

xmin, xmax = X_pca[:, 0].min() - 0.5, X_pca[:, 0].max() + 0.5
ymin, ymax = X_pca[:, 1].min() - 0.5, X_pca[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.linspace(xmin, xmax, 220), np.linspace(ymin, ymax, 220))
puntos_pca = np.c_[xx.ravel(), yy.ravel()]
puntos_esc = pca.inverse_transform(puntos_pca)      # vuelve al espacio 5D escalado
puntos_raw = scaler.inverse_transform(puntos_esc)   # vuelve al espacio 5D original

fig, axes = plt.subplots(2, 2, figsize=(11, 9))
nombres = ["KNN", "SVC", "GradientBoosting", "GaussianNB"]
for ax, nombre in zip(axes.ravel(), nombres):
    Z = best_estimators[nombre].predict(puntos_raw).reshape(xx.shape)
    ax.contourf(xx, yy, Z, levels=[-0.5, 0.5, 1.5], alpha=0.30,
                colors=["#d5f0e9", "#f5d9d0"])
    ax.contour(xx, yy, Z, levels=[0.5], colors="black", linewidths=0.8, alpha=0.6)
    m0 = y == 0
    ax.scatter(X_pca[m0, 0], X_pca[m0, 1], s=8, c="#1f77b4", alpha=0.35, label="Vacía")
    ax.scatter(X_pca[~m0, 0], X_pca[~m0, 1], s=8, c="#d62728", alpha=0.55, label="Ocupada")
    ax.set_title(f"{nombre}  (F1 = {dfres[dfres['Modelo'] == nombre]['Mejor F1-Score'].values[0]:.4f})")
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Componente 1 (PCA)"); ax.set_ylabel("Componente 2 (PCA)")
    if nombre == "KNN":
        ax.legend(loc="lower right", fontsize=8)
fig.suptitle("Fronteras de decisión proyectadas sobre las 2 primeras componentes PCA", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(OUT, "fronteras_decision_PCA.png"), dpi=200)
plt.close(fig)

# ===========================================================================
# 9. CORRELACION ENTRE FEATURES
# ===========================================================================
corr = X.corr()
fig, ax = plt.subplots(figsize=(6.5, 5.2))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels(corr.columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr.columns))); ax.set_yticklabels(corr.columns)
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=8)
ax.set_title("Correlación entre variables predictoras")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "correlacion_features.png"), dpi=200)
plt.close(fig)

print("\nGRAFICOS generados en:", OUT)
print(sorted(os.listdir(OUT)))