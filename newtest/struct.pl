 struct Breed =>
    {
        
        name  => $,
        
        
        cross => $, 
        sub a{
            $a = 5;
            return $a;
        },
        sub c{
            $ab = 9;
            $bc = 2;
            return $ab;
        }
        

    };

$cat = Breed->new(name=> "scsse", cross=>1);    
$b = $cat->c();

print $b;