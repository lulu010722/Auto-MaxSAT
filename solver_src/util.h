#ifndef _UTIL_H_
#define _UTIL_H_

#include "basis_pms.h"
#include "deci.h"

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

#endif