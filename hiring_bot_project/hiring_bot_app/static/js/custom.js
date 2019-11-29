function add_to_cart(id) {
   var product_id = id
   var quantity =$('#quantity').val()
   $.ajax({
	 url: "/add_to_cart",
	 type: "GET",
	 data: {"product_id":product_id,'quantity':quantity},
	 success: function (result) {
	          alert('Successfully added')
	         }
   })
}

$('.wish_list').on('click', function() {
   var id = $(this).attr('id')
   $.ajax({
	 url: "/add_to_wishlist",
	 data: {"product_id":id},
	 success: function (result) {
	          if(result=="Sorry can't add, already exist in Wishlist")
                  {
                   alert(result)
                  }
	          else
                  {
                    alert('Successfully added')
                  }

	         }
   })
})

function wish_list_add_to_cart(id)
{
    var id =id
    $.ajax({
		url: "/wish_list_add_to_cart",
		data: { 'id' : id },
		success: function(){
			$('#'+id).closest('tr').remove()
		},
		error: function(response){
			alert("error ");
		}

	});
}

$('.wish_list_delete').on('click', function() {
	var id = $(this).attr('id');
	$.ajax({
		url: "/wish_list_item_delete",
		data: { 'id' : id },
		success: function(){
			$('#'+id).closest('tr').remove()
		},
		error: function(response){
			alert("error ");
		}

	});
})


$('.cart_quantity_delete').on('click', function() {
	var id = $(this).attr('id');
	$.ajax({
		url: "/cart_item_delete",
		data: { 'id' : id },
		success: function(){
			$('#'+id).closest('tr').remove()
			checkout()
		},
		error: function(response){
			alert("error ");
		}

	});
})

function quantityValue(product,id,price,quantity)
{
    var value=$('#'+'a'+product).val()
    var product_id=product
    var quantity=quantity
    var price=price
    if (id==1) {
       if(value<quantity){
        value++;
         }
       else{ alert("Can't increase the quantity,Insufficient inventory.") }
    }
    if (id==0) {
       if (value>1) {
        value--;
        }
    }
    $.ajax({
     url: "/quantity_update",
     type: "GET",
     data: {'quantity':value,'product_id':product_id},
     success: function (result) {
             $('#'+'a'+product_id).val(result)
             cost=(result*price)
             $('#'+'price'+product_id).html(cost)
             checkout()
             }
             })
     return false;
}



percent_off=0
$('#coupon_code').on('click', function() {
    var coupon_code = $('#coupon_value').val();
    $.ajax({
        url: "/cart_coupon_code",
        data: { 'coupon_code' : coupon_code },
        success: function(context)
        {
            percent_off=JSON.parse(context)["percent_off"]
            coupon_valid=JSON.parse(context)["coupon_valid"]
            if (coupon_valid==1){
            $('#coupon_error').html('**Coupon code Applied!!');
            $('#coupon_error').css('color','green');
            }
            else {
            $('#coupon_error').html('**Coupon code Invalid!!');
            $('#coupon_error').css('color','red');
            }
            checkout()
        },
        error: function(){
            alert("error");
        }
    });
})

function checkout()
     {
         var shipping_cost=0
         var cart_prices=$('span[id^="price"]').map(function() { return $(this).text() }).get()
         cart_total=cart_prices.reduce((a, b) => parseFloat(a) + parseFloat(b), 0)
         $('#'+'Cart_Sub_Total').html(cart_total)
         var tax=cart_total*0.075
         $('#'+'tax').html(tax)
         off_percent=percent_off/100
         discount=off_percent*cart_total
         $('#'+'discount').html(discount)
         if (cart_total>1000){
              shipping_cost=0
             $('#'+'shipping_cost').html('Free')
             $('#shipping_charges').val('Free')
         }
         else{
               shipping_cost=100
              $('#'+'shipping_cost').html(100)
              $('#shipping_charges').val(100)
         }
         var total=cart_total+tax-discount+shipping_cost
         $('#'+'total').html(total)
         $('#grand_total').val(total)

     }

$(document).ready(function(){
    checkout()
})

function address_delete(id)
{
    var id =id
    $.ajax({
        url: "/address_delete",
		data: {'id' : id},
		success: function(result)
		{
		$('#'+ id).remove()
         }
    });
}

function set_default_address(id)
{
   var address_id = id
   $.ajax({
        url: "/set_default_address",
		data: { 'address_id':address_id },
   });
}

function same_as_above()
{
   var status=$("input[name ='billing']:checked").val()
   $('input[name="shipping"]:checked').each(function() {
   id=this.value
   if (status == 1)
   {
      $( "#"+id).prop('checked', true);
   }
});
}

$('#order_status').on('click', function() {
    var order_id = $('#order_id').val();
    var email = $('#email').val();
    $.ajax({
        url: "/order_status",
		data: { 'order_id': order_id,'email':email},
		success: function(result)
		{
		 if (result=='InValid Email')
		    {
             alert('Invalid Email')
		    }
		 else if (result=='InValid Order ID')
		    {
             alert('Invalid Order ID')
		    }
		 else
		    {
             $('#status').html(result);
             }
         }
   });
   return false;
})



