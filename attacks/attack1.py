#from math import exp, log
import numpy as np
import matplotlib.pyplot as plt


class deniable_traffic_analysis:
    deniable_filter = 0.0
    deniable_seq_len = 0

    def __init__(self, **kwargs):
        if 'filter' in kwargs.keys():
            self.deniable_filter = kwargs['filter']
        
        if 'minimum_length' in kwargs.keys():
            self.deniable_seq_len = kwargs['minimum_length']
        
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

    def find_deniable_subsequences(self, sample, lambda_param):
        probs = self.calc_deniable_likelihood(sample, lambda_param)
        subsequences = self.make_subsequences(probs)
        pruned = self.prune_subsequences(subsequences)
        return pruned
        
    def make_subsequences(self, list):
        sublists = []
        temp = []
        
        for time, prob in list:
            if prob > self.deniable_filter:
                temp.append((time, prob))
            else:
                if temp:
                    sublists.append(temp)
                    temp = []
        
        if temp:
            sublists.append(temp)
        
        return sublists
    
    def prune_subsequences(self, subsequences):
        pruned = []
        for sequence in subsequences:
            if len(sequence) >= self.deniable_seq_len:
                pruned.append(sequence)

        return pruned
        
if __name__ == '__main__':
    reg_msg_median_delay = 180
    reg_msg_count = 50000
    den_msg_median_delay = 120
    den_msg_count = 100
    den_filter = 0.55
    den_len = 6

    dta = deniable_traffic_analysis(filter=den_filter, minimum_length=den_len)
    print(f"Deniable filter = {dta.deniable_filter}")

    regular_imd = dta.make_random_imd(reg_msg_median_delay, reg_msg_count)
    deniable_imd = dta.make_random_imd(den_msg_median_delay, den_msg_count)
    validation_regular_imd = dta.make_random_imd(reg_msg_median_delay, den_msg_count)

    total_imd = regular_imd + deniable_imd
    lambda_param = dta.calc_mle(total_imd)
    res = dta.calc_deniable_likelihood(deniable_imd, lambda_param)
    val = dta.calc_deniable_likelihood(validation_regular_imd, lambda_param)
    
    den_subseq = dta.find_deniable_subsequences(deniable_imd, lambda_param)
    
    total_elements = 0
    for seq in den_subseq:
        count = len(seq)
        print(f"Subseq with length {count}")
        total_elements += count
    print("Deniable set")
    print(f"Count before = {len(deniable_imd)}, Count after = {total_elements}, Number of subsequences = {len(den_subseq)}")

    den_subseq = dta.find_deniable_subsequences(validation_regular_imd, lambda_param)
    
    total_elements = 0
    for seq in den_subseq:
        count = len(seq)
        total_elements += count
    print("Validation set")
    print(f"Count before = {len(validation_regular_imd)}, Count after = {total_elements}, Number of subsequences = {len(den_subseq)}")

    # TODO: Evaluate precisio, recall and accuracy
    # #How often the positive classification is correct.
    # print(f"Precision = {tp / (tp + fp)}") 
    
    # #How many of the actual positive cases are classified as positive.
    # print(f"Recall = {tp / (tp + fn)}") 
    
    # #The fraction of the time when the classifier gives the correct classification.
    # print(f"Accuracy = {(tp + tn) / (tp + fp + tn + fn)}") 

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
