# from ...utils.logs.fit_output_manager import FitOutputManager
from ..abstract_algo import AbstractAlgo
import tqdm

class AbstractFitAlgo(AbstractAlgo):

    def __init__(self):
        super().__init__()
        self.current_iteration = 0  # TODO change to None ?

    ###########################
    ## Core
    ###########################

    def run(self, model, data):

        # Initialize Model
        self._initialize_seed(self.seed)

        # Initialize first the random variables
        # TODO : Check if needed - model.initialize_random_variables(data)

        # Then initialize the Realizations (from the random variables)
        realizations = model.get_realization_object(data.n_individuals)

        # Smart init the realizations
        realizations = model.smart_initialization_realizations(data, realizations)

        # Initialize Algo
        self._initialize_algo(data, model, realizations)

        if self.algo_parameters['progress_bar']:
            self.display_progress_bar(-1, self.algo_parameters['n_iter'], suffix='iterations')

        # Iterate
        for it in tqdm(range(self.algo_parameters['n_iter'])):
            self.iteration(data, model, realizations)
            # if self.output_manager is not None:  # TODO better this, should work with nones
            #   self.output_manager.iteration(self, data, model, realizations)
            self.current_iteration += 1
            if self.algo_parameters['progress_bar']:
                self.display_progress_bar(it, self.algo_parameters['n_iter'], suffix='iterations')

        if 'diag_noise' in model.loss:
            noise_map = {ft_name: '{:.4f}'.format(ft_noise) for ft_name, ft_noise in zip(model.features, model.parameters['noise_std'].view(-1).tolist())}
            print_noise = repr(noise_map).replace("'", "")
        else:
            print_noise = '{:.4f}'.format(model.parameters['noise_std'].item())
        print("The standard deviation of the noise at the end of the calibration is " + print_noise)

        return realizations

    def _maximization_step(self, data, model, realizations):
        """
        Maximization step as in the EM algorith.
        In practice parameters are set to current realizations (burn-in phase),
        or as a barycenter with previous realizations.
        :param data:
        :param model:
        :param realizations:
        :return:
        """
        burn_in_phase = self._is_burn_in()  # The burn_in is true when the maximization step is memoryless
        if burn_in_phase:
            model.update_model_parameters(data, realizations, burn_in_phase)
        else:
            sufficient_statistics = model.compute_sufficient_statistics(data, realizations)
            burn_in_step = 1. / (self.current_iteration - self.algo_parameters['n_burn_in_iter'] + 1)
            self.sufficient_statistics = {k: v + burn_in_step * (sufficient_statistics[k] - v)
                                          for k, v in self.sufficient_statistics.items()}
            model.update_model_parameters(data, self.sufficient_statistics, burn_in_phase)

    def _is_burn_in(self):
        """
        Check if current iteration is in burn-in phase.
        :return:
        """
        return self.current_iteration < self.algo_parameters['n_burn_in_iter']

    ###########################
    ## Output
    ###########################

    def __str__(self):
        out = ""
        out += "=== ALGO ===\n"
        out += "Iteration {0}".format(self.current_iteration)
        return out
