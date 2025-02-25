#from math import exp, log
import numpy as np
import matplotlib.pyplot as plt


class deniable_traffic_analysis:
    deniable_filter = 0.0
    
    def __init__(self, **kwargs):
        if 'filter' in kwargs.keys():
            self.deniable_filter = kwargs['filter']
        


        self.deniable_filter


    def make_random_imd(self, median, length) -> list[float]:
        lambda_param = np.log(2) / median
        rng = np.random.default_rng()
        exp_data = rng.exponential(scale=1 / lambda_param, size=length)
        return exp_data.tolist()

    def calc_mle(self, imd: list[float]) -> float:
        return 1 / (sum(imd) / len(imd))

    def calc_deniable_likelihood(self, sample_imd: list[float], lambda_param: float) -> list[tuple[float, float]]:
        res = list()
        def cdf(x: int, var_lambda: float) -> float:
            return 1 - np.exp(-var_lambda*x)

        for sample in sample_imd:
            res.append((sample, 1 - cdf(sample, lambda_param)))
        
        return res
        # print(f"rate = {1/lambda_param}")

if __name__ == '__main__':
    reg_msg_median_delay = 180
    reg_msg_count = 50000
    den_msg_median_delay = 90
    den_msg_count = 100

    dta = deniable_traffic_analysis(filter=0.55)

    regular_imd = dta.make_random_imd(reg_msg_median_delay, reg_msg_count)
    deniable_imd = dta.make_random_imd(den_msg_median_delay, den_msg_count)
    validation_regular_imd = dta.make_random_imd(reg_msg_median_delay, den_msg_count)

    total_imd = regular_imd + deniable_imd
    lambda_param = dta.calc_mle(total_imd)
    res = dta.calc_deniable_likelihood(deniable_imd, lambda_param)
    val = dta.calc_deniable_likelihood(validation_regular_imd, lambda_param)
    
    # 0.55 seems to be a decent filter in regards to precision and recall. Accuracy is not that important
    den_filter = 0.55

    tp = 0
    fn = 0
    for x, y in res:
        if y > den_filter:
            tp += 1
        else:
            fn += 1

    tn = 0
    fp = 0
    for x, y in val:
        if y > den_filter:
            fp += 1
        else:
            tn += 1

    print(f"True positives = {tp}, False negatives = {fn}")
    print(f"True negatives = {tn}, False positives = {fp}")

    #How often the positive classification is correct.
    print(f"Precision = {tp / (tp + fp)}") 
    
    #How many of the actual positive cases are classified as positive.
    print(f"Recall = {tp / (tp + fn)}") 
    
    #The fraction of the time when the classifier gives the correct classification.
    print(f"Accuracy = {(tp + tn) / (tp + fp + tn + fn)}") 

    # Plot histogram
    #plt.hist(total_imd, bins=30, density=True, alpha=0.6, color='b')

    # Plot theoretical PDF
    x = np.linspace(0, 20, 20)
    pdf = lambda_param * np.exp(-lambda_param * x)
    cdf = 1 - np.exp(-lambda_param * x)
    plt.plot(x, pdf, 'r', linewidth=2)
    plt.plot(x, cdf, 'r', linewidth=2)

    den_lambda = dta.calc_mle(deniable_imd)
    pdf2 = den_lambda * np.exp(-den_lambda * x)
    cdf2 = 1 - np.exp(-den_lambda * x)
    plt.plot(x, pdf2, 'g', linewidth=2)
    plt.plot(x, cdf2, 'g', linewidth=2)

    plt.xlabel('Value')
    plt.ylabel('Density')
    plt.title('Exponential Distribution')

    plt.savefig("plots/plot.png", format="png", dpi=300, bbox_inches="tight")

    
    #plt.show()






