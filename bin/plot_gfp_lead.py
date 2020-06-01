from utils import *

import pandas as pd
import seaborn as sns
from sklearn.metrics import roc_auc_score

def parse_log(model, fname, brightness_offset=3.,
              start_prefix='0\tS', end_prefix='39899\tS'):
    data = []

    if model == 'gp' or 'hybrid' in model:
        uncertainty = 'GP-based uncertainty'
    elif 'mlper5g' in model or model == 'bayesnn':
        uncertainty = 'Other uncertainty'
    else:
        uncertainty = 'No uncertainty'

    if model in { 'gp', 'gp0', 'linear' }:
        seed = 1
    else:
        seed = None

    in_data = False
    with open(fname) as f:

        while True:
            line = f.readline()
            if not line:
                break

            if line.startswith('GFP Seed:\t'):
                seed = int(line.rstrip().split()[-1])

            if line.startswith(start_prefix):
                in_data = True

            if in_data:
                assert(seed is not None)
                fields = line.rstrip().split('\t')
                rank = int(fields[0]) + 1
                brightness = float(fields[-1]) + brightness_offset
                data.append([
                    model, uncertainty, rank, brightness, seed,
                ])

            if line.startswith(end_prefix):
                in_data = False

    return data

def plot_gfp(models):
    data = []
    for model in models:
        fname = ('gfp_{}.log'.format(model))
        data += parse_log(model, fname)

    df = pd.DataFrame(data, columns=[
        'model', 'uncertainty', 'order', 'brightness', 'seed',
    ])

    n_leads = [ 5, 50, 500, 5000 ]

    for n_lead in n_leads:
        df_subset = df[df.order <= n_lead]

        plt.figure()
        sns.barplot(x='model', y='brightness', data=df_subset, ci=95,
                    order=models, hue='uncertainty', dodge=False,
                    palette=sns.color_palette("RdBu", n_colors=8,),
                    capsize=0.2,)
        plt.ylim([ 3., 4. ])
        plt.savefig('figures/gfp_lead_{}.svg'.format(n_lead))
        plt.close()

        gp_brights = df_subset[df_subset.model == 'gp'].brightness
        for model in models:
            if model == 'gp':
                continue
            other_brights = df_subset[df_subset.model == model].brightness
            print('{} leads, t-test, GP vs {}:'.format(n_lead, model))
            print('\tt = {:.4f}, P = {:.4g}'
                  .format(*ss.ttest_ind(gp_brights, other_brights,
                                        equal_var=False)))
        print('')


    plt.figure()
    for model in models:
        df_subset = df[(df.model == model) & (df.seed == 1)]
        order = np.array(df_subset.order).ravel()
        brightness = np.array(df_subset.brightness).ravel()

        order_idx = np.argsort(order)
        order = order[order_idx]
        brightness = brightness[order_idx]

        n_positive, n_positives = 0, []
        for i in range(len(order)):
            if brightness[i] > 3:
                n_positive += 1
            n_positives.append(n_positive)
        plt.plot(order, n_positives)
    frac_positive = sum(brightness > 3) / float(len(brightness))
    plt.plot(order, frac_positive * order, c='gray', linestyle='--')
    plt.legend(models + [ 'Random guessing' ])
    plt.savefig('figures/gfp_acquisition.svg')

def plot_gfp_fpbase(models):
    data = []
    for model in models:
        fname = ('gfp_fpbase_{}.log'.format(model))
        data += parse_log(model, fname, brightness_offset=0.,
                          start_prefix='0\t', end_prefix='174\t')

    df = pd.DataFrame(data, columns=[
        'model', 'uncertainty', 'order', 'brightness', 'seed',
    ])

    seeds = sorted(set(df.seed))

    data = []
    for model in models:
        for seed in seeds:
            df_subset = df[(df.model == model) &
                           (df.seed == seed)]
            if len(df_subset) == 0:
                continue
            uncertainty = set(df_subset.uncertainty).pop()
            y_true = (np.array(df_subset.brightness).ravel() > 0.) * 1.
            y_pred = -np.array(df_subset.order).ravel()
            auroc = roc_auc_score(y_true, y_pred)
            data.append([ model, uncertainty, auroc, ])

    df_plot = pd.DataFrame(data, columns=[
        'model', 'uncertainty', 'value',
    ])

    plt.figure()
    sns.barplot(x='model', y='value', data=df_plot, ci=None,
                order=models, hue='uncertainty', dodge=False,
                palette=sns.color_palette("RdBu", n_colors=8))
    sns.swarmplot(x='model', y='value', data=df_plot, color='black',
                  order=models)
    plt.ylim([ 0., 1. ])
    plt.savefig('figures/gfp_fpbase_auroc.svg')
    plt.close()

if __name__ == '__main__':
    models = [
        'gp',
        'dhybrid',
        'bayesnn',
        'mlper5g',
        'mlper1',
        'linear',
    ]

    plot_gfp(models)

    #plot_gfp_fpbase(models)
