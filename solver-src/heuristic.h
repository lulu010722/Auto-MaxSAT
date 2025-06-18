int USW::pick_var()
{
    if (unsatvar_stack_fill_pointer == 0) {
        if (goodvar_stack_fill_pointer > 0) {
            return goodvar_stack[rand() % goodvar_stack_fill_pointer];
        }
        return 0;
    }

    int best_var = unsatvar_stack[0];
    long long best_score = break_score[best_var] - make_score[best_var];

    for (int i = 1; i < unsatvar_stack_fill_pointer; ++i) {
        int v = unsatvar_stack[i];
        long long score = break_score[v] - make_score[v];
        if (score > best_score || (score == best_score && time_stamp[v] < time_stamp[best_var])) {
            best_score = score;
            best_var = v;
        }
    }

    return best_var;
}

}

int USW::nearestPowerOfTen(double num)
{
    double exponent = std::log10(num);
    int floorExponent = std::floor(exponent);
    int ceilExponent = std::ceil(exponent);
    double floorPower = std::pow(10, floorExponent);
    double ceilPower = std::pow(10, ceilExponent);
    if (num - floorPower < ceilPower - num) {
        return static_cast<int>(floorPower);
    } else {
        return static_cast<int>(ceilPower);
    }
}

long long USW::closestPowerOfTen(double num)
{
    if (num <= 5) return 1;

    int n = ceil(log10(num));
    int x = round(num / pow(10, n-1));

    if (x == 10) {
        x = 1;
        n += 1;
    }

    return pow(10, n-1) * x;
}

long long USW::floorToPowerOfTen(double x)
{
    if (x <= 0.0) // if x <= 0, then return 0.
    {
        return 0;
    }
    int exponent = (int)log10(x);
    double powerOfTen = pow(10, exponent);
    long long result = (long long)powerOfTen;
    if (x < result)
    {
        result /= 10;
    }
    return result;
}

void USW::local_search_with_decimation(char *inputfile)
{
    if (1 == problem_weighted)
    {
        if (0 != num_hclauses) // weighted partial 
        {
            coe_tuned_weight = 1.0/(double)floorToPowerOfTen(double(top_clause_weight - 1) / (double)(num_sclauses));

            for (int c = 0; c < num_clauses; c++)
            {
                if (org_clause_weight[c] != top_clause_weight)
                {
                    tuned_org_clause_weight[c] = (double)org_clause_weight[c] * coe_tuned_weight;
                }
            }
        }
        else // weighted not partial
        {
            softclause_weight_threshold = 0;
            soft_smooth_probability = 1E-3;
            hd_count_threshold = 22;
            rdprob = 0.036;
            rwprob = 0.48;
            s_inc = 1.0;
            
            coe_tuned_weight = ((double)coe_soft_clause_weight)/floorToPowerOfTen((double(top_clause_weight - 1) / (double)(num_sclauses)));

            cout << "c coe_tuned_weight: " << coe_tuned_weight << endl;
            for (int c = 0; c < num_clauses; c++)
            {
                tuned_org_clause_weight[c] = (double)org_clause_weight[c] * coe_tuned_weight;
            }
        }
    }
    else 
    {
        if (0 == num_hclauses)  // unweighted not partial
        {
            hd_count_threshold = 94;
            coe_soft_clause_weight = 397;
            rdprob = 0.007;
            rwprob = 0.047;
            soft_smooth_probability = 0.002;
            softclause_weight_threshold = 550;
        }
    }
    Decimation deci(var_lit, var_lit_count, clause_lit, org_clause_weight, top_clause_weight);
    deci.make_space(num_clauses, num_vars);

    opt_unsat_weight = __LONG_LONG_MAX__;
    for (tries = 1; tries < max_tries; ++tries)
    {
        deci.init(local_opt_soln, best_soln, unit_clause, unit_clause_count, clause_lit_count);
        deci.unit_prosess();
        init(deci.fix);

        long long local_opt = __LONG_LONG_MAX__;
        max_flips = max_non_improve_flip;
        for (step = 1; step < max_flips; ++step)
        {
            if (hard_unsat_nb == 0)
            {
                local_soln_feasible = 1;
                if (local_opt > soft_unsat_weight)
                {
                    local_opt = soft_unsat_weight;
                    max_flips = step + max_non_improve_flip;
                }
                if (soft_unsat_weight < opt_unsat_weight)
                {
                    opt_time = get_runtime();
                    // cout << "o " << soft_unsat_weight << " " << total_step << " " << tries << " " << soft_smooth_probability << " " << opt_time << endl;
                    cout << "o " << soft_unsat_weight << endl;
                    opt_unsat_weight = soft_unsat_weight;

                    for (int v = 1; v <= num_vars; ++v)
                        best_soln[v] = cur_soln[v];
                    if (opt_unsat_weight <= best_known)
                    {
                        cout << "c best solution found." << endl;
                        if (opt_unsat_weight < best_known)
                        {
                            cout << "c a better solution " << opt_unsat_weight << endl;
                        }
                        return;
                    }
                }
                if (best_soln_feasible == 0)
                {
                    best_soln_feasible = 1;
                    // break;
                }
            }
            // if(goodvar_stack_fill_pointer==0) cout<<step<<": 0"<<endl;
            /*if (step % 1000 == 0)
            {
                double elapse_time = get_runtime();
                if (elapse_time >= cutoff_time)
                    return;
                else if (opt_unsat_weight == 0)
                    return;
            }*/
            int flipvar = pick_var();
            flip(flipvar);
            time_stamp[flipvar] = step;
            total_step++;
        }
    }
}

}

}

}

}

}

void USW::update_clause_weights()
{
    if (num_hclauses > 0) // partial
    {
        // update hard clause weight
        hard_increase_weights();
        if (0 == hard_unsat_nb)
        {
            soft_increase_weights_partial();
        }
    }
    else  // not partial
    {
        if (((rand() % MY_RAND_MAX_INT) * BASIC_SCALE) < soft_smooth_probability && soft_large_weight_clauses_count > soft_large_clause_count_threshold)
        {
            soft_smooth_weights();
        }
        else
        {
            soft_increase_weights_not_partial();
        }
    }
}

#endif
