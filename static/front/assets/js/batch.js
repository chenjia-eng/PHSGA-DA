// (function ($) {



//     $("#upload1").click(function (event) {
//         event.preventDefault();
//         $("#upload1").attr('disabled', 'disabled');
//         var csrftoken_input = $("meta[name='csrf-token']");
//         var csrftoken = csrftoken_input.attr("content");
//         $("#pre-loader").show();
//         var file = $("#file_upload")[0].files[0];
//         console.log(file);
//         var form = new FormData();
//         form.append("file", file);
//         // console.log(csrftoken);
//         $.ajaxSetup({
//             'beforeSend':function(xhr,settings) {
//                 if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
//                     var csrftoken = $('meta[name=csrf-token]').attr('content');
//                     xhr.setRequestHeader("X-CSRFToken", csrftoken)
//                 }
//             }
//         });


//         $.ajax({
//             url:'/api/file_predict',
//             type:'POST',
//             processData: false,
//             contentType: false,
//             data:form,
//             success:function (data) {
//                 if (data['code'] == 200) {
//                     var path = " http://127.0.0.1:5000/detail/" + data['data']
//                     console.log(path);
//                     $('#alert_message1').empty();
//                     var alert = '<div class="col-12 alert alert-success alert-dismissible" role="alert"><strong>success! </strong> Specific detailed results: <a style="color: blue" href='+path+'>'+path+'</a> <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
//                     $('#alert_message1').append(alert);
//                     $("#pre-loader").hide();
//                 }

//                 if (data['code'] == 400) {
//                     $("#upload1").removeAttr('disabled');
//                     $('#alert_message1').empty();
//                     var alert = '<div class="col-12 alert alert-danger alert-dismissible fade show" role="alert"><strong>error! </strong>'+ data['msg']  +'<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
//                     $('#alert_message1').append(alert);
//                     $("#pre-loader").hide();
//                 }
//             },
//             fail:function (error) {
//                 $("#upload1").removeAttr('disabled');
//                 $('#alert_message1').empty();
//                 var alert = '<div class="col-12 alert alert-danger alert-dismissible fade show" role="alert"><strong>error!</strong> Network anomaly, please contact the administrator.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
//                 $('#alert_message1').append(alert);
//                 $("#pre-loader").hide();
//             }



//         })


//     });


//     $("#upload2").click(function (event) {
//         event.preventDefault();
//         $("#upload2").attr('disabled', 'disabled');
//         $("#pre-loader").show();
//         var form = new FormData();
//         form.append("uuid", $("#taskid").val());
//         $.ajaxSetup({
//             'beforeSend':function(xhr,settings) {
//                 if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
//                     var csrftoken = $('meta[name=csrf-token]').attr('content');
//                     xhr.setRequestHeader("X-CSRFToken", csrftoken)
//                 }
//             }
//         });


//         $.ajax({
//             url:'/api/retrieve',
//             type:'POST',
//             processData: false,
//             contentType: false,
//             data:form,
//             success:function (data) {
//                 console.log(data);
//                 if(data['code']==200) {
//                     location.href="/detail/"+data['id'];
//                 } else {
//                     $("#upload2").removeAttr('disabled');
//                     $('#alert_message2').empty();
//                     var alert = '<div class="col-12 alert alert-danger alert-dismissible fade show" role="alert"><strong>error!</strong>  '+data['msg']+'<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
//                     $('#alert_message2').append(alert);
//                     $("#pre-loader").hide();
//                 }

//             },
//             fail:function (error) {
//                 $("#upload2").removeAttr('disabled');
//                 $('#alert_message2').empty();
//                 var alert = '<div class="col-12 alert alert-danger alert-dismissible fade show" role="alert"><strong>error!</strong> Network anomaly, please contact the administrator.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
//                 $('#alert_message2').append(alert);
//                 $("#pre-loader").hide();
//             }



//         })
//     })

// })(jQuery);


/**
 * batch.js
 * 适用于 PHSGA-DA 预测页面（物种特异性 + 通用预测双模式）
 * 依赖：jQuery, Bootstrap (用于 alert 样式)
 */

(function ($) {
    "use strict";

    // =========================================================
    // CSRF 配置（适用于 Flask-WTF 等框架）
    // =========================================================
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                var csrftoken = $('meta[name=csrf-token]').attr('content');
                if (csrftoken) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }
    });

    // =========================================================
    // 辅助函数：显示提示消息
    // =========================================================
    function showAlert(containerId, type, message) {
        // type: 'success' | 'danger' | 'info'
        $('#' + containerId).empty();
        var icon = type === 'success' ? '✓ ' : '⚠ ';
        var alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <strong>${icon}</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        $('#' + containerId).append(alertHtml);
    }

    // =========================================================
    // 辅助函数：清除提示
    // =========================================================
    function clearAlert(containerId) {
        $('#' + containerId).empty();
    }

    // =========================================================
    // 文件导入按钮联动（触发隐藏的 file input）
    // =========================================================
    $("#importFileSpecies").on("click", function () {
        $("#file_upload_species").click();
    });

    $("#importFileGeneral").on("click", function () {
        $("#file_upload_general").click();
    });

    // 可选：当文件选择后，在按钮旁边显示文件名
    $("#file_upload_species").on("change", function () {
        var fileName = $(this).val().split('\\').pop();
        if (fileName) {
            $(this).siblings(".file-hint").text(fileName);
        }
    });

    $("#file_upload_general").on("change", function () {
        var fileName = $(this).val().split('\\').pop();
        if (fileName) {
            $(this).siblings(".file-hint").text(fileName);
        }
    });

    // =========================================================
    // 物种特异性预测 —— 提交
    // =========================================================
    $("#submitSpecies").on("click", function (event) {
        event.preventDefault();

        // 1. 验证物种是否选择
        var species = $("#species_select").val();
        if (!species) {
            showAlert('alert_species', 'danger', 'Please select a species before submitting.');
            return;
        }

        // 2. 获取文件或序列
        var fileInput = $("#file_upload_species")[0];
        var sequence = $("#sequence_species").val().trim();
        var hasFile = fileInput.files && fileInput.files.length > 0;

        if (!hasFile && !sequence) {
            showAlert('alert_species', 'danger', 'Please upload a FASTA file or paste a sequence.');
            return;
        }

        // 3. 构造 FormData
        var formData = new FormData();
        formData.append("species", species);

        if (hasFile) {
            formData.append("file", fileInput.files[0]);
            formData.append("type", "1");   // 文件上传模式
        } else {
            formData.append("seq", sequence);
            formData.append("type", "0");   // 序列输入模式
        }

        // 4. UI 状态
        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Submitting...');
        clearAlert('alert_species');
        $("#pre-loader").show();

        // 5. 发送请求
        $.ajax({
            url: '/api/file_predict',   // 物种特异性接口
            type: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.code === 200) {
                    var detailUrl = "/detail/" + data.data;
                    showAlert('alert_species', 'success',
                        'Job submitted successfully! <a href="' + detailUrl + '" target="_blank">Click here to view results</a>');
                    // 可选：清空输入
                    // $("#sequence_species").val('');
                    // $("#file_upload_species").val('');
                } else {
                    var errorMsg = data.msg || 'Unknown error occurred.';
                    showAlert('alert_species', 'danger', errorMsg);
                }
            },
            error: function (xhr, status, error) {
                console.error('Submit error:', status, error);
                showAlert('alert_species', 'danger', 'Network error, please try again later.');
            },
            complete: function () {
                $btn.prop('disabled', false).html('<i class="fas fa-play"></i> Submit');
                $("#pre-loader").hide();
            }
        });
    });

    // =========================================================
    // 物种特异性预测 —— 检索任务
    // =========================================================
    $("#retrieveSpecies").on("click", function (event) {
        event.preventDefault();

        var taskId = $("#taskid_species").val().trim();
        if (!taskId) {
            showAlert('alert_species', 'danger', 'Please enter a valid task ID.');
            return;
        }

        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
        clearAlert('alert_species');
        $("#pre-loader").show();

        var formData = new FormData();
        formData.append("uuid", taskId);

        $.ajax({
            url: '/api/retrieve',
            type: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.code === 200) {
                    window.location.href = "/detail/" + data.id;
                } else {
                    showAlert('alert_species', 'danger', data.msg || 'Task not found or expired.');
                }
            },
            error: function () {
                showAlert('alert_species', 'danger', 'Network error, please try again.');
            },
            complete: function () {
                $btn.prop('disabled', false).html('<i class="fas fa-search"></i> Browse');
                $("#pre-loader").hide();
            }
        });
    });

    // =========================================================
    // 通用预测 —— 提交
    // =========================================================
    $("#submitGeneral").on("click", function (event) {
        event.preventDefault();

        var fileInput = $("#file_upload_general")[0];
        var sequence = $("#sequence_general").val().trim();
        var hasFile = fileInput.files && fileInput.files.length > 0;

        if (!hasFile && !sequence) {
            showAlert('alert_general', 'danger', 'Please upload a FASTA file or paste a sequence.');
            return;
        }

        var formData = new FormData();
        if (hasFile) {
            formData.append("file", fileInput.files[0]);
            formData.append("type", "1");
        } else {
            formData.append("seq", sequence);
            formData.append("type", "0");
        }

        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Submitting...');
        clearAlert('alert_general');
        $("#pre-loader").show();

        $.ajax({
            url: '/api/uploadMamba',   // 通用预测接口
            type: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.code === 200) {
                    var detailUrl = "/detail/" + data.data;
                    showAlert('alert_general', 'success',
                        'Job submitted successfully! <a href="' + detailUrl + '" target="_blank">Click here to view results</a>');
                } else {
                    var errorMsg = data.msg || 'Unknown error occurred.';
                    showAlert('alert_general', 'danger', errorMsg);
                }
            },
            error: function () {
                showAlert('alert_general', 'danger', 'Network error, please try again later.');
            },
            complete: function () {
                $btn.prop('disabled', false).html('<i class="fas fa-play"></i> Submit');
                $("#pre-loader").hide();
            }
        });
    });

    // =========================================================
    // 通用预测 —— 检索任务
    // =========================================================
    $("#retrieveGeneral").on("click", function (event) {
        event.preventDefault();

        var taskId = $("#taskid_general").val().trim();
        if (!taskId) {
            showAlert('alert_general', 'danger', 'Please enter a valid task ID.');
            return;
        }

        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
        clearAlert('alert_general');
        $("#pre-loader").show();

        var formData = new FormData();
        formData.append("uuid", taskId);

        $.ajax({
            url: '/api/retrieve',
            type: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.code === 200) {
                    window.location.href = "/detail/" + data.id;
                } else {
                    showAlert('alert_general', 'danger', data.msg || 'Task not found or expired.');
                }
            },
            error: function () {
                showAlert('alert_general', 'danger', 'Network error, please try again.');
            },
            complete: function () {
                $btn.prop('disabled', false).html('<i class="fas fa-search"></i> Browse');
                $("#pre-loader").hide();
            }
        });
    });

    // =========================================================
    // 初始化：页面加载时隐藏 pre-loader
    // =========================================================
    $(document).ready(function () {
        $("#pre-loader").hide();
    });

})(jQuery);