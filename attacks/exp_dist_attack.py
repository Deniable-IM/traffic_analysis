import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import pandas as pd
import attacks.utils.pcap_to_pd_reader as reader

class deniable_traffic_generator:
    def make_random_exp_dist_imd(self, median, length) -> list[float]:
        lambda_param = np.log(2) / median
        rng = np.random.default_rng()
        exp_data = rng.exponential(scale=1 / lambda_param, size=length)
        return exp_data.tolist()

    def make_random_ppp_imd(self, lambda_param, length) -> list[float]:
        rng = np.random.default_rng()
        return rng.poisson(lam=lambda_param, size=length).tolist()


class exp_dist_attack:
    deniable_filter = 0
    deniable_seq_len = 0

    def __init__(self, **kwargs):
        if 'filter' in kwargs.keys():
            self.deniable_filter = kwargs['filter']
        
        if 'minimum_length' in kwargs.keys():
            self.deniable_seq_len = kwargs['minimum_length']

    def calc_mle(self, imd: list[float]) -> float:
        return 1 / (sum(imd) / len(imd))

    def calc_deniable_likelihood(self, sample_imd: list[float], lambda_param: float) -> list[tuple[float, float]]:
        res = list()
        def cdf(x: float, var_lambda: float) -> float:
            return 1 - np.exp(-var_lambda*x)

        for sample in sample_imd:
            res.append((sample, 1 - cdf(sample, lambda_param)))
        
        return res

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

def multi_eval(args):
    process_count = mp.cpu_count()
    splits = int(args['iterations'] / process_count)
    tasks = []
    pipe_list = []
    args['iterations'] = splits

    for split in range(0, process_count):
        if split != []:
            recv_end, send_end = mp.Pipe(False)
            t = mp.Process(target=evaluate_approach, args=(send_end,), kwargs=arg)
            tasks.append(t)
            pipe_list.append(recv_end)
            t.start()

    # Receive dicts from processes and merge
    merged_dict = {"seq_signal": 0, "seq_noise": 0, "var_signal": 0, "var_noise": 0}
    for (i, task) in enumerate(tasks):
        d = pipe_list[i].recv()
        task.join()
        for key, value in d.items():
            merged_dict[key] += value

    print(merged_dict)
    print(f"Seq S/N = {merged_dict['seq_signal'] / merged_dict['seq_noise']}, Var S/N = {merged_dict['var_signal'] / merged_dict['var_noise']}")
    return merged_dict


def evaluate_approach(send_end, **kwargs):
    den_len = kwargs['den_len']
    den_filter = kwargs['den_filter']
    reg_msg_count = kwargs['reg_count']
    reg_msg_median_delay = kwargs['reg_delay']
    den_msg_count = kwargs['den_count']
    den_msg_median_delay = kwargs['den_delay']
    iterations = kwargs['iterations']
    dtg = deniable_traffic_generator()
    dta = exp_dist_attack(filter=den_filter, minimum_length=den_len)
    print(f"Deniable filter = {dta.deniable_filter}, Deniable sequence minimum length = {dta.deniable_seq_len}, Iterations = {iterations}")
    
    seq_signal = 0
    seq_noise = 0
    var_signal = 0
    var_noise = 0
    for i in range(0, iterations):
        regular_imd = dtg.make_random_exp_dist_imd(reg_msg_median_delay, reg_msg_count)
        deniable_imd = dtg.make_random_exp_dist_imd(den_msg_median_delay, den_msg_count)
        validation_regular_imd = dtg.make_random_exp_dist_imd(reg_msg_median_delay, den_msg_count)
        total_imd = regular_imd + deniable_imd
        lambda_param = dta.calc_mle(total_imd)
        
        den_subseq = dta.find_deniable_subsequences(deniable_imd, lambda_param)
        seq_signal += len(den_subseq)
        for seq in den_subseq:
            var_signal += len(seq)

        reg_subseq = dta.find_deniable_subsequences(validation_regular_imd, lambda_param)
        seq_noise += len(reg_subseq)
        for seq in reg_subseq:
            var_noise += len(seq)

    send_end.send({"seq_signal": seq_signal, "seq_noise": seq_noise, "var_signal": var_signal, "var_noise": var_noise})  



if __name__ == '__main__':
    reg_msg_median_delay = 180
    reg_msg_count = 50000
    den_msg_median_delay = 90
    den_msg_count = 100
    den_filter = max(0.55, den_msg_median_delay / reg_msg_median_delay)
    den_len = 5
    iterations = 10000
    #res = evaluate_approach(iterations = iterations, reg_delay = reg_msg_median_delay, reg_count = reg_msg_count, den_delay = den_msg_median_delay, den_count = den_msg_count, den_filter = den_filter, den_len = den_len)
    arg = {"iterations": iterations, "reg_delay": reg_msg_median_delay, "reg_count": reg_msg_count, "den_delay": den_msg_median_delay, "den_count": den_msg_count, "den_filter": den_filter, "den_len": den_len}


    dtg = deniable_traffic_generator()
    dta = exp_dist_attack(filter=den_filter, minimum_length=den_len)
    reg_imd = dtg.make_random_ppp_imd(100, 50000)
    den_imd = dtg.make_random_ppp_imd(60, 100)

    res = dta.find_deniable_subsequences(den_imd, dta.calc_mle(reg_imd))

    rd = reader.pcap_reader()

    df = rd.load_pcapng_to_pd("random_cap.pcapng")
    print(df)

    # TODO: Evaluate precisio, recall and accuracy
    # #How often the positive classification is correct.
    # print(f"Precision = {tp / (tp + fp)}") 
    
    # #How many of the actual positive cases are classified as positive.
    # print(f"Recall = {tp / (tp + fn)}") 
    
    # #The fraction of the time when the classifier gives the correct classification.
    # print(f"Accuracy = {(tp + tn) / (tp + fp + tn + fn)}") 


    # TODO: Make visualizer
    # Plot histogram
    #plt.hist(total_imd, bins=30, density=True, alpha=0.6, color='b')


    # # Plot theoretical PDF
    # x = np.linspace(0, 20, 20)
    # pdf = lambda_param * np.exp(-lambda_param * x)
    # cdf = 1 - np.exp(-lambda_param * x)
    # plt.plot(x, pdf, 'r', linewidth=2)
    # plt.plot(x, cdf, 'r', linewidth=2)

    # den_lambda = dta.calc_mle(deniable_imd)
    # pdf2 = den_lambda * np.exp(-den_lambda * x)
    # cdf2 = 1 - np.exp(-den_lambda * x)
    # plt.plot(x, pdf2, 'g', linewidth=2)
    # plt.plot(x, cdf2, 'g', linewidth=2)

    # plt.xlabel('Value')
    # plt.ylabel('Density')
    # plt.title('Exponential Distribution')

    # plt.savefig("plots/plot.png", format="png", dpi=300, bbox_inches="tight")

    
    #plt.show()
