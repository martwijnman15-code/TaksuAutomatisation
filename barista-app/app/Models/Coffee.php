<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasOne;
use App\Models\Order;

class Coffee extends Model
{
    protected $guarded = [];

    public function order(): HasOne
    {
        return $this->hasOne(Coffee::class);
    }
}
