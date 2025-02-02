import numpy as np
import matplotlib.pyplot as plt


def pyplot_setup():
  '''
  Pyplot setup
  '''
  plt.rcParams['pgf.preamble'] = r'\usepackage{amsfonts}'
  plt.rcParams['pgf.texsystem'] = 'pdflatex'
  plt.rcParams['pgf.rcfonts'] = False
  plt.rcParams['text.latex.preamble'] = r'\usepackage{amsfonts}'
  plt.rcParams['text.usetex'] = True
  plt.rcParams['font.size'] = '9'
  plt.rcParams['font.family'] = 'serif'

  return

def plugin_ece(scores, labels, num_bins, p=2, debias=True):
  '''
  Input:
    scores: (Z_1, ... , Z_n) \in [0, 1]^n
    labels: (Y_1, ..., Y_n) \in {0, 1}^n
    num_bins: m
    debias: If True, debias plug-in estimator (only works for p = 2)
  Output:
    Plug-in estimator of l_p-ECE(f)^p w.r.t. m equal-width bins
  '''
  indexes = np.floor(num_bins * scores).astype(int)
  counts = np.bincount(indexes)
  counts[counts == 0] += 1

  if p == 2 and debias:
    error = (((np.bincount(indexes, weights=scores) - np.bincount(indexes, weights=labels))**2
              - np.bincount(indexes, weights=(scores - labels)**2)) / counts).sum()
  else:
    error = (np.abs(np.bincount(indexes, weights=scores) - np.bincount(indexes, weights=labels))**p / counts).sum()

  return error / len(scores)


def perturb_scores(scores, num_perturbations, smoothness, signs, scale):
  '''
  Input:
    scores: (Z_1, ... , Z_n) \in [0, 1]^n
    num_perturbations: m
    smoothness: Holder exponent s
    signs: Perturbation signs (a_1, ... , a_n) \in {-1, 1}^n
    scale: rho

  Output:
    (g(Z_1), ... , g(Z_n)) where g(Z_i) = Z_i + a_i * rho * m^(-s) * zeta({2 * m * Z_i}) if 0.25 <= Z_i <= 0.75
                                 g(Z_i) = Z_i otherwise
  '''
  is_inner = (0.25 <= scores) & (scores <= 0.75)
  zeta = lambda x: scale * np.exp(-1 / x / (1 - x))
  rescale = lambda x: 2 * num_perturbations * (x - 0.25) - np.floor(2 * num_perturbations * (x - 0.25))
  perturbations = is_inner * num_perturbations**(-smoothness) * zeta(rescale(scores)) * signs
  
  return scores + perturbations


def chi_squared(sample1, sample2, num_bins):
  '''
  Input:
    sample1: (V_1, ... , V_{n_1}) \in [0, 1]^{n_1}
    sample2: (W_1, ... , W_{n_2}) \in [0, 1]^{n_2}
    num_bins: m
  Output:
    Two-sample chi-squared statistic w.r.t. m equal-width bins
  '''
  n1 = len(sample1)
  n2 = len(sample2)
  indexes1 = np.floor(num_bins * sample1).astype(int)
  indexes2 = np.floor(num_bins * sample2).astype(int)

  stat = ((np.bincount(indexes1, minlength=num_bins) / n1 - np.bincount(indexes2, minlength=num_bins) / n2)**2).sum()

  return stat


def rejection_sampling(scores, labels):
  '''
  Input:
    scores: (Z_1, ... , Z_n) \in [0, 1]^n
    labels: (Y_1, ... , Y_n) \in {0, 1}^n
  Output:
    Split the scores and perform rejection sampling based on labels/pseudo-labels (see Section 3.3).
    Output (V_1, ... , V_{n_1}), (W_1, ... , W_{n_2})
  '''
  size = len(scores)
  
  scores1 = scores[:size//2]
  labels1 = labels[:size//2]
  scores2 = scores[size//2:]
  labels2 = np.random.binomial(1, scores2)
  idx1 = labels1 == 1
  idx2 = labels2 == 1
  
  return scores1[idx1], scores2[idx2]


def consistency_resampling(scores):
  '''
  Input:
    scores: (Z_1, ... , Z_n) \in [0, 1]^n
  Output:
    Sample (Z_1', ... , Z_n') with replacement from {Z_1, ... , Z_n}
    Output (Y_1', ... , Y_n') where Y_i' ~ Ber(Z_i')
  '''
  n = len(scores)
  sampled_scores = np.random.choice(scores, size=n, replace=True)
  sampled_labels = np.random.binomial(1, sampled_scores, n)

  return sampled_scores, sampled_labels
