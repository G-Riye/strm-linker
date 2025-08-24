// 扫描配置功能调试脚本
// 用于测试和验证修复后的功能

console.log('=== 扫描配置功能调试 ===');

// 模拟API响应数据结构
const mockApiResponse = {
  configs: [
    {
      config_id: '1',
      name: '测试配置1',
      description: '这是一个测试配置',
      directory: '/test/path',
      recursive: true,
      custom_video_extensions: ['mp4', 'mkv'],
      custom_metadata_extensions: ['nfo', 'srt'],
      created_at: '2024-01-01T00:00:00Z'
    }
  ]
};

const mockExecutionResult = {
  directory: '/test/path',
  processed: 5,
  created_links: 3,
  skipped: 2,
  errors: [
    { file: 'test1.strm', error: '权限不足' },
    { file: 'test2.strm', error: '文件不存在' }
  ],
  details: [
    {
      file: 'movie.(mp4).strm',
      result: {
        base_name: 'movie',
        video_extension: 'mp4',
        links_created: 2,
        created_links: ['movie.(mp4).nfo', 'movie.(mp4).jpg']
      }
    }
  ],
  duration: 1.5
};

// 验证数据结构
function validateDataStructure(data, name) {
  console.log(`\n--- 验证 ${name} ---`);
  
  if (Array.isArray(data)) {
    console.log(`✅ ${name} 是数组，长度: ${data.length}`);
    data.forEach((item, index) => {
      console.log(`  项目 ${index}:`, item);
    });
  } else if (data && typeof data === 'object') {
    console.log(`✅ ${name} 是对象`);
    Object.keys(data).forEach(key => {
      console.log(`  ${key}:`, data[key]);
    });
  } else {
    console.log(`❌ ${name} 不是预期的数据结构:`, data);
  }
}

// 测试数据验证
console.log('\n=== 测试数据验证 ===');
validateDataStructure(mockApiResponse.configs, '配置列表');
validateDataStructure(mockExecutionResult.errors, '错误列表');
validateDataStructure(mockExecutionResult.details, '详情列表');

// 模拟Vue组件中的数据处理
function processConfigData(configs) {
  if (!Array.isArray(configs)) {
    console.log('❌ 配置列表不是数组，返回空数组');
    return [];
  }
  
  return configs.filter(config => 
    config && 
    typeof config === 'object' && 
    config.config_id && 
    config.name
  );
}

function processExecutionResult(result) {
  if (!result || typeof result !== 'object') {
    console.log('❌ 执行结果无效，返回默认值');
    return {
      directory: '',
      processed: 0,
      created_links: 0,
      skipped: 0,
      errors: [],
      details: [],
      duration: 0
    };
  }
  
  return {
    directory: result.directory || '',
    processed: result.processed || 0,
    created_links: result.created_links || 0,
    skipped: result.skipped || 0,
    errors: Array.isArray(result.errors) ? result.errors : [],
    details: Array.isArray(result.details) ? result.details : [],
    duration: result.duration || 0
  };
}

// 测试数据处理
console.log('\n=== 测试数据处理 ===');
const processedConfigs = processConfigData(mockApiResponse.configs);
console.log('处理后的配置:', processedConfigs);

const processedResult = processExecutionResult(mockExecutionResult);
console.log('处理后的执行结果:', processedResult);

// 测试错误情况
console.log('\n=== 测试错误情况 ===');
const invalidConfigs = processConfigData(null);
console.log('无效配置数据:', invalidConfigs);

const invalidResult = processExecutionResult(null);
console.log('无效执行结果:', invalidResult);

console.log('\n=== 调试完成 ===');
console.log('如果看到所有 ✅ 标记，说明数据结构验证通过');
console.log('修复后的组件应该能够正确处理这些数据而不会出现属性名错误');
