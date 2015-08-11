//JS functionality
//Developed by Juan Camilo Gutierrez - 1/August/2015
$('fn').ready(function(){
	// Filters that shows the content of the typed word.
	$('#filter-item-table').keyup(function() {
		var query = $(this).val(),
		    local_text = ''
		$("tr").css('display','table-row')
		$("tr a.item-name").filter(function (index,el) {
			
			local_text = el.text.toLowerCase();
			query = query.toLowerCase();
            return local_text.indexOf(query)==-1
		}).parents("tr").css('display','none')
	});
	$('#filter-category-table').keyup(function() {
		var query = $(this).val(),
		    local_text = ''
		$("tr").css('display','table-row')
		$("tr a.category-name").filter(function (index,el) {
			
			local_text = el.text.toLowerCase();
			query = query.toLowerCase();
            return local_text.indexOf(query)==-1
		}).parents("tr").css('display','none')
	});

	//Back buttons
	$(".back-buttons").click(function() {
		window.history.back()
	})
    //This small JavaScript piece of code, sets the value of the category to the select menu.
    var v = $("#value-category").val()
     $("select.category-edit-item option").filter(function (index,el) {
         return el.value == v
     }).attr('selected','selected');
     //Triggres the input file
    $(".button-image-item").click(function() {
    	$(".image-item").trigger("click")
    });
    $(".delete-items").click(function() {
    	var data = $(this).attr('data-id'),
    		remove = confirm('Are sure you want to remove this item?')
    	if(remove)
    		location.href="/remove-item/" +data
    })
})