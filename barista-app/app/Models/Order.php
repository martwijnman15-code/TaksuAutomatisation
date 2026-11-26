<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use App\Models\Coffee;

class Order extends Model
{
    protected $guarded = [];

    public function coffees(): HasMany
    {
        return $this->hasMany(Coffee::class);
    }
}