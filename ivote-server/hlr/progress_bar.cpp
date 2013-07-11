/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Written in 2004-2013 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#include "progress_bar.h"

#include <stdio.h>

ProgressBar::ProgressBar(int max)
{
	my_max = max;
	my_curr = 0;
	my_level = 0;
	tmp_level = 0;
}

ProgressBar::~ProgressBar()
{
}

void ProgressBar::next(const std::string& out)
{
	my_curr++;

	tmp_level = (my_curr * 100) / my_max;

	if (tmp_level != my_level) {
		my_level = tmp_level;
		fprintf(stdout, "%s: %d%%\r", out.c_str(), my_level);
		if (my_level == 100) {
			fprintf(stdout, "\n");
		}
		fflush(stdout);
	}
}

