<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Coffee;
use Illuminate\Http\Request;

class CoffeeController extends Controller
{
    public function __construct(
        protected CoffeeService $service
    ) {}

    /**
     * Display a listing of the resource.
     */
    public function index()
    {
        return response()->json(CoffeeResource::collection(
            Coffee::all()
        ));
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'required|string|max:1000',
            'is_coffee' => 'required',
        ]);

        return response()->json($this->service->create(
            $data
        ));
    }

    /**
     * Display the specified resource.
     */
    public function show(Coffee $coffee)
    {
        return response()->json($this->service->show(
            $coffee
        ));
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, Coffee $coffee)
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'required',
        ]);

        return response()->json($this->service->update(
            $coffee,
            $data
        ));
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(Coffee $coffee)
    {
        Coffee::first(id, $coffee->id)->delete();
        return response()->noContent();
    }
}
